import unittest
from copy import deepcopy
from typing import Mapping
from warnings import catch_warnings

import torch
from torch import nn, fx
from torch.fx import symbolic_trace
from torchvision.models.resnet import resnet18, resnet34

from nn_lib.models.graph_module_plus import GraphModulePlus
from nn_lib.models.graph_utils import prefix_all_nodes
from nn_lib.models.utils import frozen


class ModuleTestCase(unittest.TestCase):
    def assertModulesEqual(self, modA: nn.Module, modB: nn.Module):
        """Helper function to assert that two modules are identical."""
        self.assertSequenceEqual(
            [k for k, _ in modA.named_parameters()],
            [k for k, _ in modB.named_parameters()],
        )
        self.assertSequenceEqual(
            [k for k, _ in modA.named_modules()],
            [k for k, _ in modB.named_modules()],
        )

        stateA = modA.state_dict()
        stateB = modB.state_dict()
        for keyA, paramA in stateA.items():
            self.assertIn(keyA, stateB, f"Key {keyA} not found in stateB")
            paramB = stateB[keyA]
            self.assertTrue(
                torch.equal(paramA, paramB),
                f"Parameters for key {keyA} are not equal",
            )


class FakeStitchingLayerForTesting(nn.Module):
    def __init__(self, in_f, out_f):
        super().__init__()
        self.conv = nn.Conv2d(in_f, out_f, kernel_size=1, padding=0, stride=1)

    def forward(self, x):
        return self.conv(x)

    def update_weight(self, mul):
        self.conv.weight.data *= mul


class DummyModuleWithMethodsAndAssertions(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, x: torch.Tensor):
        # This forward() function is designed to test symbolic tracing of method calls. The first
        # is a method call on a tensor. The second is a function call on a package.

        # Call a method on a tensor
        sz = x.dim()

        # Make a traceable assertion
        torch._assert(sz == 2, "requires 2D tensor input")

        # Call a method of torch
        x = torch.permute(x, (1, 0))

        return x


class TestGraphModulePlus(ModuleTestCase):

    def setUp(self):
        # Setup code to initialize a GraphModulePlus instance and any necessary nodes
        self.reference_module = resnet18()
        self.gm = GraphModulePlus.new_from_trace(self.reference_module)
        self.dummy_input = torch.randn(1, 3, 224, 224)

    def _get_dummy_rep(self, node_name):
        return GraphModulePlus.new_from_copy(self.gm).set_output(node_name)(self.dummy_input)

    def test_superseded(self):
        # Thanks to the @supersedes decorator, even built-in fx code that would normally return a
        # fx.GraphModule should return a GraphModulePlus instead
        gm = symbolic_trace(self.reference_module)
        self.assertIsInstance(gm, GraphModulePlus)

    def test_inputs(self):
        inputs = self.gm.inputs
        self.assertEqual(len(inputs), 1)
        self.assertEqual(inputs[0].name, "x")

    def test_output(self):
        self.assertEqual(self.gm.output.name, "output")
        self.assertEqual(self.gm.output_value.name, "fc")

    def test_set_inputs(self):
        # With eliminate_dead, the method should just work without warnings
        og_rep = self._get_dummy_rep("maxpool")
        og_output = self.gm(self.dummy_input)
        with catch_warnings(record=True) as w:
            self.gm.set_inputs(["maxpool"])
        print("Warnings:", *w, sep="\n")
        self.assertEqual(len(w), 0)
        inputs = self.gm.inputs
        self.assertEqual(len(inputs), 1)
        self.assertEqual(inputs[0].name, "maxpool")
        new_output = self.gm(og_rep)
        torch.testing.assert_close(og_output, new_output)

    def test_set_output(self):
        og_result = self._get_dummy_rep("layer1_1_relu")
        num_nodes_before = len(list(self.gm.graph.nodes))
        the_node = self.gm._resolve_nodes("layer1_1_relu")[0]
        self.gm.set_output("layer1_1_relu")
        self.assertEqual(self.gm.output_value, the_node)

        num_nodes_after = len(list(self.gm.graph.nodes))
        self.assertLess(num_nodes_after, num_nodes_before)

        new_result = self.gm(self.dummy_input)
        torch.testing.assert_close(og_result, new_result)

    def test_set_dict_outputs(self):
        self.gm.set_dict_outputs(outputs=["add_1", "add_2", "add_3"])
        out = self.gm(self.dummy_input)
        self.assertTrue(isinstance(out, dict))
        self.assertEqual(len(out), 3)
        self.assertIn("add_1", out)
        self.assertIn("add_2", out)
        self.assertIn("add_3", out)
        self.assertTrue(isinstance(out["add_1"], torch.Tensor))
        self.assertTrue(isinstance(out["add_2"], torch.Tensor))
        self.assertTrue(isinstance(out["add_3"], torch.Tensor))

    def test_set_inputs_and_output_noop(self):
        num_nodes_before = len(list(self.gm.graph.nodes))
        dummy_output_before = self.gm(self.dummy_input)

        self.gm.set_inputs_and_output(self.gm.inputs, self.gm.output_value)

        num_nodes_after = len(list(self.gm.graph.nodes))
        dummy_output_after = self.gm(self.dummy_input)

        self.assertEqual(num_nodes_before, num_nodes_after)
        self.assertTrue(torch.allclose(dummy_output_before, dummy_output_after))

    def test_squash_conv_bn(self):
        self.gm.eval()
        output_before = self.gm(self.dummy_input)
        new_gm = self.gm.squash_all_conv_batchnorm_pairs()
        output_after = new_gm(self.dummy_input)

        def is_softmax_close(a, b):
            return torch.allclose(torch.softmax(a, dim=-1), torch.softmax(b, dim=-1), atol=1e-6)

        self.assertTrue(is_softmax_close(output_before, output_after))

        # The thing about batchnorm is that in 'training' mode, it updates itself on any forward
        # call. So we can check it all BN were eliminated by verifying that outputs are not changing
        # during train mode.
        new_gm.train()
        new_gm(self.dummy_input)
        output_after_2 = new_gm(self.dummy_input)
        self.assertTrue(is_softmax_close(output_after, output_after_2))

    def test_freeze_subgraph(self):
        params_before = {k: v.clone() for k, v in self.gm.named_parameters()}
        with frozen(self.gm.extract_subgraph(inputs=["add_1"], output="add_5")):
            opt = torch.optim.SGD(self.gm.parameters(), lr=0.1)
            for _ in range(10):
                opt.zero_grad()
                self.gm(self.dummy_input).sum().backward()
                opt.step()

        params_after = {k: v.clone() for k, v in self.gm.named_parameters()}

        for k in params_before:
            # We chose 'add_1' and 'add_5' above because they bracket the layer2 and layer3 parts
            # of the resnet18 model. So we expect the parameters in those blocks to be frozen.
            if k.startswith("layer2") or k.startswith("layer3"):
                self.assertTrue(
                    torch.allclose(params_before[k], params_after[k]),
                    f"Expected {k} to be frozen",
                )
            else:
                self.assertFalse(
                    torch.allclose(params_before[k], params_after[k]),
                    f"Expected {k} to be updated",
                )

        # Outside the with context, train again and assert that everything changed
        opt = torch.optim.SGD(self.gm.parameters(), lr=0.1)
        for _ in range(10):
            opt.zero_grad()
            self.gm(self.dummy_input).sum().backward()
            opt.step()

        params_after_after = {k: v.clone() for k, v in self.gm.named_parameters()}

        for k in params_after:
            self.assertFalse(
                torch.allclose(params_after[k], params_after_after[k]),
                f"Expected {k} to be updated",
            )

    def test_merge_graphmodules_leaves_originals_unchanged(self):
        """Merging to create a new GraphModulePlus should not modify the original models. Since
        new_from_merge contains cases for model type, this test isolates the case where the models
        are themselves instances of GraphModulePlus.
        """
        modelA = GraphModulePlus.new_from_trace(resnet18())
        modelB = GraphModulePlus.new_from_trace(resnet34())

        # Make a deepcopy snapshot of all the attrs of modelA and modelB so we can assert later
        # that merging did not modify the original models
        modelA_copy, modelB_copy = deepcopy(modelA), deepcopy(modelB)

        _ = GraphModulePlus.new_from_merge(
            modules={"modelA": modelA, "modelB": modelB},
            rewire_inputs={"modelB_layer2_1_relu_1": "modelA_add_3"},
            auto_trace=True,
        )

        self.assertModulesEqual(modelA_copy, modelA)
        self.assertModulesEqual(modelB_copy, modelB)

    def test_merge_modules_leaves_originals_unchanged(self):
        """Same as the previous test, but now with tracing some standard nn.Module models."""
        modelA = resnet18()
        modelB = resnet34()

        # Make a deepcopy snapshot of all the attrs of modelA and modelB so we can assert later
        # that merging did not modify the original models
        modelA_copy, modelB_copy = deepcopy(modelA), deepcopy(modelB)

        _ = GraphModulePlus.new_from_merge(
            modules={"modelA": modelA, "modelB": modelB},
            rewire_inputs={"modelB_layer2_1_relu_1": "modelA_add_3"},
            auto_trace=True,
        )

        self.assertModulesEqual(modelA_copy, modelA)
        self.assertModulesEqual(modelB_copy, modelB)

    def test_merge_two_modules_auto_trace(self):
        modelA, modelB = resnet18(), resnet34()
        merged_model = GraphModulePlus.new_from_merge(
            modules={"modelA": modelA, "modelB": modelB},
            rewire_inputs={"modelB_layer2_1_relu_1": "modelA_add_3"},
            auto_trace=True,
        )

        self.assertEqual(merged_model.__class__.__name__, "MergedResNetResNet")

        # Make sure we can still run the model and get outputs without crashing
        merged_model(self.dummy_input)

        # With auto_trace, we expect the merged model to have lots of nodes (copying ops from
        # modelA and from modelB).
        self.assertGreater(len(merged_model.graph.nodes), 100)

        # Nodes downstream of the rewire in A or upstream in B should no longer exist
        with self.assertRaises(ValueError):
            merged_model._resolve_nodes("modelA_add_4")

        with self.assertRaises(ValueError):
            merged_model._resolve_nodes("modelB_add_1")

    def test_merge_three_modules_stitching(self):
        modelA = GraphModulePlus.new_from_trace(resnet18())
        modelB = GraphModulePlus.new_from_trace(resnet34())
        targetB = modelB.insert_noop("add_3")
        stitcher = FakeStitchingLayerForTesting(128, 128)
        merged_model = GraphModulePlus.new_from_merge(
            modules={"modelA": modelA, "stitching_layer": stitcher, "modelB": modelB},
            rewire_inputs={
                "stitching_layer": "modelA_add_2",
                f"modelB_{targetB}": "stitching_layer",
            },
            auto_trace=False,
        )

        self.assertEqual(
            merged_model.__class__.__name__, "MergedResNetFakeStitchingLayerForTestingResNet"
        )

        # Nodes downstream of the rewire in A or upstream in B should no longer exist
        with self.assertRaises(ValueError):
            merged_model._resolve_nodes("modelA_add_4")

        with self.assertRaises(ValueError):
            merged_model._resolve_nodes("modelB_add_1")

        # We should still have access to the stitching layer's methods, and it should affect the
        # merged model's behavior because the underlying parameters are shared.
        out1 = merged_model(self.dummy_input)
        merged_model.stitching_layer.update_weight(0.5)
        out2 = merged_model(self.dummy_input)

        self.assertFalse(torch.allclose(out1, out2))

    def test_merge_three_modules_stitching_auto_trace(self):
        """Same as the previous test, but now with auto_trace=True. It's expected behavior that
        we can no longer access the update_weight method of the *traced* stitching layer. A
        to-do for someday is to make it so that we can still access the methods of the original
        modules even when tracing.
        """
        modelA = GraphModulePlus.new_from_trace(resnet18())
        modelB = GraphModulePlus.new_from_trace(resnet34())
        stitcher = FakeStitchingLayerForTesting(512, 128)
        merged_model = GraphModulePlus.new_from_merge(
            modules={"modelA": modelA, "stitching_layer": stitcher, "modelB": modelB},
            rewire_inputs={
                "stitching_layer_conv": "modelA_add_2",
                "modelB_layer2_1_relu_1": "stitching_layer_conv",
            },
            auto_trace=True,
        )

        self.assertEqual(
            merged_model.__class__.__name__, "MergedResNetFakeStitchingLayerForTestingResNet"
        )

        with self.assertRaises(AttributeError):
            merged_model.stitching_layer.update_weight(0.5)

    def test_prefix_leaves_original_unchanged(self):
        """Assert that prefix_all_nodes treats its inputs as immutable."""
        my_gm = GraphModulePlus.new_from_trace(resnet18())
        gm_nodes_before = set(map(str, my_gm.graph.nodes))
        new_graph = prefix_all_nodes(my_gm.graph, prefix="pre")
        new_nodes_after = set(map(str, new_graph.nodes))
        gm_nodes_after = set(map(str, my_gm.graph.nodes))

        self.assertNotEqual(gm_nodes_before, new_nodes_after, "Node names should all be different")
        self.assertEqual(gm_nodes_before, gm_nodes_after, "Original graph should not be modified")

    def test_prefix_simple(self):
        new_graph = prefix_all_nodes(self.gm.graph, prefix="pre")
        new_gm = GraphModulePlus(root=nn.ModuleDict({"pre": self.gm}), graph=new_graph)

        self.assertTrue(hasattr(new_gm, "pre"))
        self.assertTrue(hasattr(self.gm, "conv1"))
        self.assertTrue(hasattr(new_gm.pre, "conv1"))

        og_out = self.gm(self.dummy_input)
        new_out = new_gm(self.dummy_input)
        torch.testing.assert_close(og_out, new_out)

    def test_prefix_call_module(self):
        dummy_gm = GraphModulePlus.new_from_trace(DummyModuleWithMethodsAndAssertions())
        new_graph = prefix_all_nodes(dummy_gm.graph, prefix="pre")
        new_gm = GraphModulePlus(root=nn.ModuleDict({"pre": dummy_gm}), graph=new_graph)

        dummy_input = torch.ones(4, 3)
        og_out = dummy_gm(dummy_input)
        new_out = new_gm(dummy_input)
        torch.testing.assert_close(og_out, new_out)

    def test_copy_is_not_deep(self):
        param_before = next(iter(self.gm.parameters()))
        param_before.data[:] = 1.0
        torch.testing.assert_close(param_before.data, torch.ones_like(param_before.data))

        gm2 = GraphModulePlus.new_from_copy(self.gm)
        param2 = next(iter(gm2.parameters()))
        param2.data[:] = 2.0

        torch.testing.assert_close(param_before.data, torch.ones_like(param2.data) * 2)

    def test_copy_does_not_delete(self):
        og_num_nodes = len(list(self.gm.graph.nodes))
        og_out = self.gm(self.dummy_input)
        truncated_copy = GraphModulePlus.new_from_copy(self.gm).set_output("add_3")

        # The copy should have fewer nodes...
        self.assertLess(len(list(truncated_copy.graph.nodes)), og_num_nodes)

        # ...but should not have modified the original
        self.assertEqual(len(list(self.gm.graph.nodes)), og_num_nodes)

        # The copy should still be able to run
        trunc_out = truncated_copy(self.dummy_input)
        self.assertEqual(trunc_out.ndim, 4)

        # The og model should still be able to run
        torch.testing.assert_close(og_out.detach(), self.gm(self.dummy_input).detach())

    def test_strip_assert(self):
        good_input = torch.ones(4, 3)
        bad_input = torch.ones(5, 4, 3)
        dummy_gm = GraphModulePlus.new_from_trace(DummyModuleWithMethodsAndAssertions())

        dummy_gm(good_input)
        with self.assertRaises(AssertionError):
            dummy_gm(bad_input)

        dummy_gm.strip_all_where(lambda node: node.is_impure and "assert" in node.name)

        dummy_gm(good_input)
        with self.assertRaises(RuntimeError):
            dummy_gm(bad_input)

    def test_delta_state_dict(self):
        copy_gm = deepcopy(self.gm)
        copy_gm.layer1._modules["0"].conv1.weight.data = torch.ones_like(
            copy_gm.layer1._modules["0"].conv1.weight
        )

        delta = copy_gm.delta_state_dict(self.gm)
        self.assertEqual(len(delta), 1)

        new_resnet = GraphModulePlus.new_from_trace(resnet18())
        new_resnet.load_delta_state_dict(delta, self.gm)

        assert torch.equal(
            new_resnet.layer1._modules["0"].conv2.weight, self.gm.layer1._modules["0"].conv2.weight
        )
        assert torch.equal(
            new_resnet.layer1._modules["0"].conv1.weight,
            torch.ones_like(copy_gm.layer1._modules["0"].conv1.weight),
        )

    def test_insert_noop(self):
        num_nodes1 = len(list(self.gm.graph.nodes))
        out1 = self.gm(self.dummy_input)
        noop_node = self.gm.insert_noop("add_4")
        num_nodes2 = len(list(self.gm.graph.nodes))
        out2 = self.gm(self.dummy_input)
        torch.testing.assert_close(out1, out2)
        self.assertEqual(num_nodes1 + 1, num_nodes2)
        self.assertIn(noop_node, self.gm.graph.nodes)
        self.assertEqual(noop_node.args[0].name, "add_4")
        self.assertGreater(len(list(noop_node.users)), 0)


if __name__ == "__main__":
    unittest.main()
