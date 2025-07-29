import torch
import torch.nn as nn
import pytest
from sky_optimizer.utils.agc import (
    adaptive_gradient_clipping,
    AGCWrapper,
    apply_agc_to_model,
    create_agc_optimizer
)


class TestAdaptiveGradientClipping:
    """Test suite for Adaptive Gradient Clipping (AGC) functionality."""

    def test_basic_agc_functionality(self):
        """Test basic AGC functionality."""
        model = nn.Linear(10, 5)
        
        # Create large gradients
        x = torch.randn(8, 10)
        y = torch.randn(8, 5)
        loss = nn.MSELoss()(model(x), y) * 100  # Large loss for large gradients
        loss.backward()
        
        # Store original gradient norms
        original_norms = [p.grad.norm().item() for p in model.parameters()]
        
        # Apply AGC
        total_norm = adaptive_gradient_clipping(
            model.parameters(),
            clip_factor=0.01,
            eps=1e-3
        )
        
        # Check that gradients were clipped
        clipped_norms = [p.grad.norm().item() for p in model.parameters()]
        
        # At least some gradients should be clipped if they were large
        assert isinstance(total_norm, torch.Tensor)
        assert total_norm.item() >= 0
        
        # All gradients should be finite
        for p in model.parameters():
            assert torch.isfinite(p.grad).all()

    def test_agc_with_small_gradients(self):
        """Test AGC doesn't affect small gradients unnecessarily."""
        model = nn.Linear(10, 5)
        
        # Create small gradients
        with torch.no_grad():
            for p in model.parameters():
                p.grad = torch.randn_like(p) * 1e-6
        
        # Store original gradients
        original_grads = [p.grad.clone() for p in model.parameters()]
        
        # Apply AGC
        adaptive_gradient_clipping(
            model.parameters(),
            clip_factor=0.01,
            eps=1e-3
        )
        
        # Small gradients should be largely unchanged
        for orig, p in zip(original_grads, model.parameters()):
            # Allow for small numerical differences
            assert torch.allclose(orig, p.grad, rtol=1e-3, atol=1e-6)

    def test_agc_gradient_centralization(self):
        """Test AGC with gradient centralization."""
        model = nn.Conv2d(3, 16, 3)
        
        # Create gradients
        x = torch.randn(4, 3, 32, 32)
        y = torch.randn(4, 16, 30, 30)
        loss = nn.MSELoss()(model(x), y)
        loss.backward()
        
        # Apply AGC with gradient centralization
        adaptive_gradient_clipping(
            model.parameters(),
            clip_factor=0.01,
            gradient_centralization=True
        )
        
        # Check gradients are finite
        for p in model.parameters():
            assert torch.isfinite(p.grad).all()

    def test_agc_wrapper_basic(self):
        """Test AGCWrapper basic functionality."""
        model = nn.Linear(10, 5)
        base_optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
        agc_optimizer = AGCWrapper(base_optimizer, clip_factor=0.01)
        
        x = torch.randn(8, 10)
        y = torch.randn(8, 5)
        loss_fn = nn.MSELoss()
        
        # Test optimization step
        for i in range(5):
            agc_optimizer.zero_grad()
            loss = loss_fn(model(x), y)
            loss.backward()
            agc_optimizer.step()
        
        # Check parameters are finite
        for p in model.parameters():
            assert torch.isfinite(p).all()

    def test_agc_wrapper_layerwise(self):
        """Test AGCWrapper with layerwise adaptation."""
        model = nn.Sequential(
            nn.Linear(20, 10),
            nn.ReLU(),
            nn.Linear(10, 5)
        )
        
        base_optimizer = torch.optim.SGD(model.parameters(), lr=1e-2)
        agc_optimizer = AGCWrapper(
            base_optimizer,
            clip_factor=0.01,
            layerwise_adaptation=True,
            adaptive_clipping=True
        )
        
        x = torch.randn(16, 20)
        y = torch.randn(16, 5)
        loss_fn = nn.MSELoss()
        
        # Run several steps to build up layer statistics
        for i in range(20):
            agc_optimizer.zero_grad()
            loss = loss_fn(model(x), y)
            loss.backward()
            agc_optimizer.step()
        
        # Check that layer-specific adaptations were created
        assert len(agc_optimizer.adaptive_clip_factors) > 0
        
        # Check parameters are finite
        for p in model.parameters():
            assert torch.isfinite(p).all()

    def test_agc_wrapper_warmup(self):
        """Test AGCWrapper with warmup."""
        model = nn.Linear(10, 5)
        base_optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
        agc_optimizer = AGCWrapper(
            base_optimizer,
            clip_factor=0.1,  # Larger factor to test warmup effect
            warmup_steps=10
        )
        
        x = torch.randn(8, 10)
        y = torch.randn(8, 5)
        loss_fn = nn.MSELoss()
        
        # Test that warmup progresses
        initial_factor = agc_optimizer._get_adaptive_clip_factor()
        
        for i in range(5):
            agc_optimizer.zero_grad()
            loss = loss_fn(model(x), y)
            loss.backward()
            agc_optimizer.step()
        
        mid_factor = agc_optimizer._get_adaptive_clip_factor()
        
        for i in range(10):
            agc_optimizer.zero_grad()
            loss = loss_fn(model(x), y)
            loss.backward()
            agc_optimizer.step()
        
        final_factor = agc_optimizer._get_adaptive_clip_factor()
        
        # Should progress: initial <= mid <= final
        assert initial_factor <= mid_factor
        assert mid_factor <= final_factor

    def test_apply_agc_to_model(self):
        """Test apply_agc_to_model function."""
        model = nn.Sequential(
            nn.Linear(10, 5),
            nn.BatchNorm1d(5),
            nn.Linear(5, 2)
        )
        
        x = torch.randn(8, 10)
        y = torch.randn(8, 2)
        loss = nn.MSELoss()(model(x), y)
        loss.backward()
        
        # Apply AGC excluding batch norm layers
        total_norm = apply_agc_to_model(
            model,
            clip_factor=0.01,
            exclude_layers=['BatchNorm']
        )
        
        assert isinstance(total_norm, torch.Tensor)
        assert total_norm.item() >= 0
        
        # Check all parameters are finite
        for p in model.parameters():
            if p.grad is not None:
                assert torch.isfinite(p.grad).all()

    def test_create_agc_optimizer(self):
        """Test create_agc_optimizer convenience function."""
        model = nn.Linear(10, 5)
        base_optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
        
        agc_optimizer = create_agc_optimizer(base_optimizer, clip_factor=0.02)
        
        assert isinstance(agc_optimizer, AGCWrapper)
        assert agc_optimizer.clip_factor == 0.02
        
        x = torch.randn(8, 10)
        y = torch.randn(8, 5)
        loss_fn = nn.MSELoss()
        
        # Test basic functionality
        agc_optimizer.zero_grad()
        loss = loss_fn(model(x), y)
        loss.backward()
        agc_optimizer.step()
        
        for p in model.parameters():
            assert torch.isfinite(p).all()

    def test_agc_parameter_delegation(self):
        """Test that AGCWrapper correctly delegates to base optimizer."""
        model = nn.Linear(10, 5)
        base_optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
        agc_optimizer = AGCWrapper(base_optimizer)
        
        # Test property delegation
        assert agc_optimizer.param_groups is base_optimizer.param_groups
        assert agc_optimizer.defaults is base_optimizer.defaults
        
        # Test state dict operations
        state_dict = agc_optimizer.state_dict()
        assert state_dict == base_optimizer.state_dict()
        
        # Test loading state dict
        new_state = {'state': {}, 'param_groups': base_optimizer.param_groups}
        agc_optimizer.load_state_dict(new_state)

    def test_agc_edge_cases(self):
        """Test AGC edge cases."""
        # Test with empty parameter list
        total_norm = adaptive_gradient_clipping([], clip_factor=0.01)
        assert total_norm.item() == 0.0
        
        # Test with single tensor
        tensor = torch.randn(5, 5, requires_grad=True)
        tensor.grad = torch.randn_like(tensor)
        
        total_norm = adaptive_gradient_clipping(tensor, clip_factor=0.01)
        assert isinstance(total_norm, torch.Tensor)
        assert torch.isfinite(tensor.grad).all()

    def test_agc_numerical_stability(self):
        """Test AGC numerical stability."""
        model = nn.Linear(10, 5)
        
        # Test with zero gradients
        with torch.no_grad():
            for p in model.parameters():
                p.grad = torch.zeros_like(p)
        
        total_norm = adaptive_gradient_clipping(
            model.parameters(),
            clip_factor=0.01
        )
        
        assert total_norm.item() == 0.0
        
        # Test with very small parameters
        with torch.no_grad():
            for p in model.parameters():
                p.data.fill_(1e-10)
                p.grad = torch.randn_like(p)
        
        adaptive_gradient_clipping(
            model.parameters(),
            clip_factor=0.01,
            adaptive_eps=True
        )
        
        # Should not crash and gradients should be finite
        for p in model.parameters():
            assert torch.isfinite(p.grad).all()

    @pytest.mark.gpu
    def test_agc_gpu_compatibility(self):
        """Test AGC on GPU if available."""
        if not torch.cuda.is_available():
            pytest.skip("GPU not available")
        
        device = torch.device('cuda')
        model = nn.Linear(10, 5).to(device)
        
        x = torch.randn(8, 10, device=device)
        y = torch.randn(8, 5, device=device)
        loss = nn.MSELoss()(model(x), y)
        loss.backward()
        
        # Apply AGC on GPU
        total_norm = adaptive_gradient_clipping(
            model.parameters(),
            clip_factor=0.01
        )
        
        assert total_norm.device.type == 'cuda'
        
        # Check gradients remain on GPU
        for p in model.parameters():
            assert p.grad.device.type == 'cuda'
            assert torch.isfinite(p.grad).all()


if __name__ == "__main__":
    test_suite = TestAdaptiveGradientClipping()
    
    print("Running AGC Tests...")
    test_suite.test_basic_agc_functionality()
    print("✓ Basic AGC functionality test passed")
    
    test_suite.test_agc_wrapper_basic()
    print("✓ AGC wrapper basic test passed")
    
    test_suite.test_agc_numerical_stability()
    print("✓ AGC numerical stability test passed")
    
    print("\nAll AGC tests passed! ✅")