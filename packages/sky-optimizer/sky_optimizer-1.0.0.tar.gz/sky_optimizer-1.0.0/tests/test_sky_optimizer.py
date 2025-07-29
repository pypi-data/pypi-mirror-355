import torch
import time
import numpy as np
import pytest
from sky_optimizer import SkyOptimizer, create_sky_optimizer


class TestSkyOptimizer:
    """Test suite for Sky Optimizer functionality."""

    def test_sky_optimizer_step(self):
        """Basic functionality test."""
        model = torch.nn.Linear(4, 2)
        opt = create_sky_optimizer(
            model,
            lr=1e-3,
            max_grad_norm=0.5,
            cyclical_lr=True,
            cycle_steps=4,
            gradient_variance_adaptation=True,
        )
        x = torch.randn(8, 4)
        y = torch.randn(8, 2)
        loss_fn = torch.nn.MSELoss()
        loss = loss_fn(model(x), y)
        loss.backward()
        opt.step()
        for p in model.parameters():
            assert not torch.isnan(p).any()
            assert not torch.isinf(p).any()

    def test_numerical_stability(self):
        """Test numerical stability with extreme values."""
        model = torch.nn.Linear(10, 5)
        opt = create_sky_optimizer(model, lr=1e-2)
        
        # Test with large gradients
        with torch.no_grad():
            for p in model.parameters():
                p.grad = torch.randn_like(p) * 100
        
        opt.step()
        
        # Check parameters remain finite
        for p in model.parameters():
            assert torch.isfinite(p).all(), "Parameters became non-finite with large gradients"
        
        # Test with tiny gradients
        with torch.no_grad():
            for p in model.parameters():
                p.grad = torch.randn_like(p) * 1e-10
        
        opt.step()
        
        for p in model.parameters():
            assert torch.isfinite(p).all(), "Parameters became non-finite with tiny gradients"

    def test_convergence_detection(self):
        """Test adaptive convergence detection."""
        model = torch.nn.Linear(2, 1)
        opt = create_sky_optimizer(model, lr=1e-2)
        
        # Simulate convergence by running many steps with decreasing loss
        x = torch.randn(100, 2)
        y = torch.randn(100, 1)
        loss_fn = torch.nn.MSELoss()
        
        for i in range(50):
            loss = loss_fn(model(x), y)
            loss.backward()
            opt.step()
            opt.zero_grad()
        
        # Test convergence detection
        if len(opt.loss_history) >= 20:
            converged, criteria = opt._adaptive_convergence_detection()
            assert isinstance(converged, bool)
            assert isinstance(criteria, dict)
            assert len(criteria) > 0

    @pytest.mark.slow
    def test_performance_benchmark(self):
        """Benchmark performance improvements."""
        # Test with a larger model
        model = torch.nn.Sequential(
            torch.nn.Linear(100, 50),
            torch.nn.ReLU(),
            torch.nn.Linear(50, 25),
            torch.nn.ReLU(),
            torch.nn.Linear(25, 1)
        )
        
        # Compare optimized vs basic configuration
        opt_basic = SkyOptimizer(
            model.parameters(),
            lr=1e-3,
            riemannian_geometry=False,
            natural_gradients=False,
            quasi_newton_methods=False,
            matrix_factorization=False
        )
        
        opt_enhanced = create_sky_optimizer(model, lr=1e-3)
        
        x = torch.randn(32, 100)
        y = torch.randn(32, 1)
        loss_fn = torch.nn.MSELoss()
        
        # Benchmark basic optimizer
        start_time = time.time()
        for i in range(10):
            loss = loss_fn(model(x), y)
            loss.backward()
            opt_basic.step()
            opt_basic.zero_grad()
        basic_time = time.time() - start_time
        
        # Reset model
        for p in model.parameters():
            p.data.normal_(0, 0.1)
        
        # Benchmark enhanced optimizer
        start_time = time.time()
        for i in range(10):
            loss = loss_fn(model(x), y)
            loss.backward()
            opt_enhanced.step()
            opt_enhanced.zero_grad()
        enhanced_time = time.time() - start_time
        
        print(f"Basic optimizer time: {basic_time:.4f}s")
        print(f"Enhanced optimizer time: {enhanced_time:.4f}s")
        print(f"Performance ratio: {enhanced_time / basic_time:.2f}x")
        
        # Enhanced should not be more than 3x slower due to additional features
        assert enhanced_time / basic_time < 3.0, "Enhanced optimizer too slow"

    @pytest.mark.slow
    def test_memory_efficiency(self):
        """Test memory efficiency improvements."""
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not available for memory testing")
        
        import gc
        
        process = psutil.Process(os.getpid())
        
        model = torch.nn.Linear(1000, 500)
        opt = create_sky_optimizer(model, lr=1e-3)
        
        # Measure initial memory
        gc.collect()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run optimization steps
        x = torch.randn(64, 1000)
        y = torch.randn(64, 500)
        loss_fn = torch.nn.MSELoss()
        
        for i in range(20):
            loss = loss_fn(model(x), y)
            loss.backward()
            opt.step()
            opt.zero_grad()
        
        # Measure memory after optimization
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Memory increase: {memory_increase:.2f} MB")
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100, f"Memory usage too high: {memory_increase:.2f} MB"

    @pytest.mark.gpu
    def test_gpu_compatibility(self):
        """Test GPU compatibility if available."""
        if not torch.cuda.is_available():
            pytest.skip("GPU not available")
        
        device = torch.device('cuda')
        model = torch.nn.Linear(100, 50).to(device)
        opt = create_sky_optimizer(model, lr=1e-3)
        
        x = torch.randn(32, 100, device=device)
        y = torch.randn(32, 50, device=device)
        loss_fn = torch.nn.MSELoss()
        
        # Test several optimization steps on GPU
        for i in range(5):
            loss = loss_fn(model(x), y)
            loss.backward()
            opt.step()
            opt.zero_grad()
        
        # Check all parameters are still on GPU and finite
        for p in model.parameters():
            assert p.device.type == 'cuda', "Parameter moved off GPU"
            assert torch.isfinite(p).all(), "Parameter became non-finite on GPU"

    def test_mathematical_features(self):
        """Test advanced mathematical features."""
        model = torch.nn.Linear(20, 10)
        opt = create_sky_optimizer(
            model,
            lr=1e-3,
            riemannian_geometry=True,
            natural_gradients=True,
            quasi_newton_methods=True,
            information_theory=True,
            matrix_factorization=True
        )
        
        x = torch.randn(16, 20)
        y = torch.randn(16, 10)
        loss_fn = torch.nn.MSELoss()
        
        # Run several steps to initialize mathematical features
        for i in range(10):
            loss = loss_fn(model(x), y)
            loss.backward()
            opt.step()
            opt.zero_grad()
        
        # Check that mathematical features are working
        for p in model.parameters():
            state = opt.state[p]
            
            # Check various state components exist
            assert 'fisher_diag' in state
            assert 'hessian_diag' in state
            assert 'metric_tensor' in state
            
            # Check they have reasonable values
            assert torch.isfinite(state['fisher_diag']).all()
            assert torch.isfinite(state['hessian_diag']).all()
            assert torch.isfinite(state['metric_tensor']).all()

    def test_optimization_metrics(self):
        """Test optimization metrics collection."""
        model = torch.nn.Linear(10, 5)
        opt = create_sky_optimizer(model, lr=1e-3)
        
        x = torch.randn(8, 10)
        y = torch.randn(8, 5)
        loss_fn = torch.nn.MSELoss()
        
        # Run optimization to collect metrics
        for i in range(15):
            loss = loss_fn(model(x), y)
            loss.backward()
            opt.step()
            opt.zero_grad()
        
        # Test metrics collection
        metrics = opt.get_optimization_metrics()
        
        assert 'performance' in metrics
        assert 'mathematical' in metrics
        assert 'meta_learning' in metrics
        assert 'landscape' in metrics
        
        assert metrics['performance']['global_step'] == 15
        assert 'lr_adaptation' in metrics['meta_learning']
        assert 'momentum_adaptation' in metrics['meta_learning']

    def test_sky_metrics(self):
        """Test Sky-specific metrics collection."""
        model = torch.nn.Linear(10, 5)
        opt = create_sky_optimizer(model, lr=1e-3)
        
        x = torch.randn(8, 10)
        y = torch.randn(8, 5)
        loss_fn = torch.nn.MSELoss()
        
        # Run optimization to collect metrics
        for i in range(10):
            loss = loss_fn(model(x), y)
            loss.backward()
            opt.step()
            opt.zero_grad()
        
        # Test Sky metrics
        metrics = opt.get_sky_metrics()
        
        assert 'global_step' in metrics
        assert 'gradient_conflicts' in metrics
        assert 'surgery_applications' in metrics
        assert 'meta_learning_state' in metrics
        assert 'landscape_metrics' in metrics
        
        assert metrics['global_step'] == 10
        assert isinstance(metrics['gradient_conflicts'], int)
        assert isinstance(metrics['surgery_applications'], int)

    def test_adaptive_gradient_clipping(self):
        """Test adaptive gradient clipping functionality."""
        model = torch.nn.Linear(10, 5)
        opt = create_sky_optimizer(
            model, 
            lr=1e-3,
            agc_clip_factor=0.01,
            agc_eps=1e-3
        )
        
        x = torch.randn(8, 10)
        y = torch.randn(8, 5)
        loss_fn = torch.nn.MSELoss()
        
        # Create large gradients
        loss = loss_fn(model(x), y) * 100
        loss.backward()
        
        # Store gradients before clipping
        grad_norms_before = [p.grad.norm().item() for p in model.parameters() if p.grad is not None]
        
        opt.step()
        
        # Check that optimization completed without issues
        for p in model.parameters():
            assert torch.isfinite(p).all()

    def test_cyclical_learning_rate(self):
        """Test cyclical learning rate functionality."""
        model = torch.nn.Linear(10, 5)
        opt = create_sky_optimizer(
            model,
            lr=1e-3,
            cyclical_lr=True,
            cycle_steps=10,
            cycle_multiplier=2.0
        )
        
        x = torch.randn(8, 10)
        y = torch.randn(8, 5)
        loss_fn = torch.nn.MSELoss()
        
        # Run for more than one cycle
        for i in range(25):
            loss = loss_fn(model(x), y)
            loss.backward()
            opt.step()
            opt.zero_grad()
        
        # Check that optimization completed
        assert opt.global_step == 25
        
        # Check meta-learning state is being updated
        assert 'lr_adaptation' in opt.meta_learning_state
        assert 'momentum_adaptation' in opt.meta_learning_state

    def test_parameter_groups(self):
        """Test optimizer works with parameter groups."""
        model = torch.nn.Sequential(
            torch.nn.Linear(10, 5),
            torch.nn.Linear(5, 2)
        )
        
        # Create parameter groups with different settings
        param_groups = [
            {'params': model[0].parameters(), 'lr': 1e-3},
            {'params': model[1].parameters(), 'lr': 5e-4}
        ]
        
        opt = SkyOptimizer(param_groups)
        
        x = torch.randn(8, 10)
        y = torch.randn(8, 2)
        loss_fn = torch.nn.MSELoss()
        
        # Test optimization with parameter groups
        for i in range(5):
            loss = loss_fn(model(x), y)
            loss.backward()
            opt.step()
            opt.zero_grad()
        
        # Check that all parameters are finite
        for p in model.parameters():
            assert torch.isfinite(p).all()

    def test_state_dict_save_load(self):
        """Test optimizer state dict save and load functionality."""
        model = torch.nn.Linear(10, 5)
        opt = create_sky_optimizer(model, lr=1e-3)
        
        x = torch.randn(8, 10)
        y = torch.randn(8, 5)
        loss_fn = torch.nn.MSELoss()
        
        # Run a few steps to create state
        for i in range(5):
            loss = loss_fn(model(x), y)
            loss.backward()
            opt.step()
            opt.zero_grad()
        
        # Save state
        state_dict = opt.state_dict()
        
        # Create new optimizer and load state
        opt2 = create_sky_optimizer(model, lr=1e-3)
        opt2.load_state_dict(state_dict)
        
        # Check that states match
        assert opt2.global_step == opt.global_step
        assert len(opt2.state) == len(opt.state)
        
        # Continue optimization with loaded state
        loss = loss_fn(model(x), y)
        loss.backward()
        opt2.step()
        opt2.zero_grad()
        
        # Check parameters remain finite
        for p in model.parameters():
            assert torch.isfinite(p).all()


class TestSkyOptimizerEdgeCases:
    """Test edge cases and error conditions."""

    def test_invalid_parameters(self):
        """Test that invalid parameters raise appropriate errors."""
        model = torch.nn.Linear(5, 2)
        
        # Test invalid learning rate
        with pytest.raises(ValueError):
            SkyOptimizer(model.parameters(), lr=-1.0)
        
        # Test invalid beta values
        with pytest.raises(ValueError):
            SkyOptimizer(model.parameters(), betas=(1.5, 0.9))
        
        with pytest.raises(ValueError):
            SkyOptimizer(model.parameters(), betas=(0.9, 1.5))
        
        # Test invalid weight decay
        with pytest.raises(ValueError):
            SkyOptimizer(model.parameters(), weight_decay=-0.1)

    def test_empty_parameters(self):
        """Test optimizer with empty parameter list."""
        opt = SkyOptimizer([])
        
        # Should not error when stepping with no parameters
        loss = opt.step()
        assert loss is None

    def test_no_gradients(self):
        """Test optimizer step when no parameters have gradients."""
        model = torch.nn.Linear(5, 2)
        opt = create_sky_optimizer(model, lr=1e-3)
        
        # Step without computing gradients
        loss = opt.step()
        assert loss is None
        
        # Parameters should remain unchanged
        for p in model.parameters():
            assert torch.isfinite(p).all()

    def test_mixed_gradient_availability(self):
        """Test optimizer with some parameters having gradients and others not."""
        model = torch.nn.Sequential(
            torch.nn.Linear(10, 5),
            torch.nn.Linear(5, 2)
        )
        opt = create_sky_optimizer(model, lr=1e-3)
        
        x = torch.randn(8, 10)
        y = torch.randn(8, 2)
        loss_fn = torch.nn.MSELoss()
        
        # Compute loss and gradients
        loss = loss_fn(model(x), y)
        loss.backward()
        
        # Manually remove gradients from first layer
        for p in model[0].parameters():
            p.grad = None
        
        # Should still work with partial gradients
        opt.step()
        
        # Check parameters remain finite
        for p in model.parameters():
            assert torch.isfinite(p).all()


if __name__ == "__main__":
    # Run basic tests
    test_suite = TestSkyOptimizer()
    
    print("Running Sky Optimizer Tests...")
    test_suite.test_sky_optimizer_step()
    print("✓ Basic functionality test passed")
    
    test_suite.test_numerical_stability()
    print("✓ Numerical stability test passed")
    
    test_suite.test_mathematical_features()
    print("✓ Mathematical features test passed")
    
    test_suite.test_optimization_metrics()
    print("✓ Optimization metrics test passed")
    
    print("\nAll basic tests passed! ✅")