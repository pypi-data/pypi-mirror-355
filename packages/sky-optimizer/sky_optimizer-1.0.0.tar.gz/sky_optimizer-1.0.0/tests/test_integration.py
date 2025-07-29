"""
Integration tests for Sky Optimizer package.
These tests validate that the entire package works together correctly.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import pytest
from sky_optimizer import SkyOptimizer, create_sky_optimizer
from sky_optimizer.utils.agc import AGCWrapper


class SimpleNet(nn.Module):
    """Simple neural network for testing."""
    
    def __init__(self, input_size=784, hidden_size=128, num_classes=10):
        super().__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, num_classes)
        self.dropout = nn.Dropout(0.2)
    
    def forward(self, x):
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return x


class ConvNet(nn.Module):
    """Convolutional neural network for testing."""
    
    def __init__(self, num_classes=10):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.dropout1 = nn.Dropout2d(0.25)
        self.dropout2 = nn.Dropout2d(0.5)
        self.fc1 = nn.Linear(9216, 128)
        self.fc2 = nn.Linear(128, num_classes)

    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)
        x = self.conv2(x)
        x = F.relu(x)
        x = F.max_pool2d(x, 2)
        x = self.dropout1(x)
        x = torch.flatten(x, 1)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout2(x)
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)


class TestSkyOptimizerIntegration:
    """Integration tests for Sky Optimizer."""

    def test_simple_training_loop(self):
        """Test complete training loop with Sky Optimizer."""
        # Create model and data
        model = SimpleNet(input_size=20, hidden_size=64, num_classes=5)
        optimizer = create_sky_optimizer(model, lr=1e-3)
        criterion = nn.CrossEntropyLoss()
        
        # Generate synthetic data
        batch_size = 32
        num_batches = 10
        
        initial_loss = None
        final_loss = None
        
        for batch_idx in range(num_batches):
            # Generate batch
            data = torch.randn(batch_size, 20)
            target = torch.randint(0, 5, (batch_size,))
            
            # Forward pass
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            
            # Store initial and final loss
            if batch_idx == 0:
                initial_loss = loss.item()
            if batch_idx == num_batches - 1:
                final_loss = loss.item()
            
            # Backward pass and optimization
            loss.backward()
            optimizer.step()
            
            # Validate parameters
            for param in model.parameters():
                assert torch.isfinite(param).all(), f"Non-finite parameter detected at batch {batch_idx}"
        
        # Check that training progressed (loss should generally decrease)
        print(f"Initial loss: {initial_loss:.4f}, Final loss: {final_loss:.4f}")
        
        # Get optimization metrics
        metrics = optimizer.get_optimization_metrics()
        assert metrics['performance']['global_step'] == num_batches
        
        # Check meta-learning adaptations
        assert 'lr_adaptation' in metrics['meta_learning']
        assert 'momentum_adaptation' in metrics['meta_learning']

    def test_conv_net_training(self):
        """Test Sky Optimizer with convolutional networks."""
        model = ConvNet(num_classes=5)
        optimizer = create_sky_optimizer(
            model, 
            lr=1e-3,
            riemannian_geometry=True,
            spectral_normalization=True,
            agc_clip_factor=0.01
        )
        criterion = nn.NLLLoss()
        
        # Generate synthetic image data
        batch_size = 16
        num_batches = 8
        
        for batch_idx in range(num_batches):
            # Generate batch (MNIST-like)
            data = torch.randn(batch_size, 1, 28, 28)
            target = torch.randint(0, 5, (batch_size,))
            
            # Training step
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            
            # Validate parameters
            for param in model.parameters():
                assert torch.isfinite(param).all()
        
        # Check mathematical features were used
        conv_params = [model.conv1.weight, model.conv2.weight]
        for param in conv_params:
            if param in optimizer.state:
                state = optimizer.state[param]
                # Should have mathematical state for conv layers
                assert 'hessian_diag' in state
                assert 'fisher_diag' in state

    def test_sky_with_agc_wrapper(self):
        """Test Sky Optimizer compatibility with AGC wrapper."""
        model = SimpleNet(input_size=50, hidden_size=32, num_classes=3)
        
        # Create Sky optimizer
        sky_optimizer = create_sky_optimizer(model, lr=1e-3, agc_clip_factor=0.0)  # Disable built-in AGC
        
        # Wrap with AGC
        optimizer = AGCWrapper(sky_optimizer, clip_factor=0.02)
        criterion = nn.CrossEntropyLoss()
        
        # Training loop
        for batch_idx in range(5):
            data = torch.randn(16, 50)
            target = torch.randint(0, 3, (16,))
            
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            
            # Check all parameters are finite
            for param in model.parameters():
                assert torch.isfinite(param).all()

    def test_parameter_groups_integration(self):
        """Test Sky Optimizer with different parameter groups."""
        model = SimpleNet(input_size=30, hidden_size=64, num_classes=4)
        
        # Create parameter groups with different settings
        param_groups = [
            {
                'params': [model.fc1.weight, model.fc1.bias],
                'lr': 1e-3,
                'weight_decay': 0.01
            },
            {
                'params': [model.fc2.weight, model.fc2.bias],
                'lr': 5e-4,
                'weight_decay': 0.005
            },
            {
                'params': [model.fc3.weight, model.fc3.bias],
                'lr': 2e-3,
                'weight_decay': 0.02
            }
        ]
        
        optimizer = SkyOptimizer(
            param_groups,
            riemannian_geometry=True,
            natural_gradients=True,
            meta_learning=True
        )
        criterion = nn.CrossEntropyLoss()
        
        # Training loop
        for batch_idx in range(10):
            data = torch.randn(24, 30)
            target = torch.randint(0, 4, (24,))
            
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            
            # Validate all parameters
            for param in model.parameters():
                assert torch.isfinite(param).all()
        
        # Check that different parameter groups have different states
        fc1_state = optimizer.state[model.fc1.weight]
        fc2_state = optimizer.state[model.fc2.weight]
        fc3_state = optimizer.state[model.fc3.weight]
        
        # All should have mathematical state
        for state in [fc1_state, fc2_state, fc3_state]:
            assert 'exp_avg' in state
            assert 'exp_avg_sq' in state
            assert 'hessian_diag' in state

    def test_large_model_scalability(self):
        """Test Sky Optimizer scalability with larger models."""
        # Create a moderately large model
        model = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 10)
        )
        
        optimizer = create_sky_optimizer(
            model,
            lr=1e-3,
            # Use efficient settings for larger models
            matrix_factorization=True,
            low_rank_approximation=20,
            spectral_normalization=True,
            agc_clip_factor=0.01
        )
        criterion = nn.CrossEntropyLoss()
        
        # Larger batches
        batch_size = 64
        num_batches = 5
        
        for batch_idx in range(num_batches):
            data = torch.randn(batch_size, 512)
            target = torch.randint(0, 10, (batch_size,))
            
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            
            # Validate parameters
            for param in model.parameters():
                assert torch.isfinite(param).all()
        
        # Check that optimization completed successfully
        metrics = optimizer.get_optimization_metrics()
        assert metrics['performance']['global_step'] == num_batches

    def test_mixed_precision_compatibility(self):
        """Test Sky Optimizer with mixed precision training."""
        try:
            from torch.cuda.amp import GradScaler, autocast
            if not torch.cuda.is_available():
                pytest.skip("CUDA not available for mixed precision test")
        except ImportError:
            pytest.skip("Mixed precision not available in this PyTorch version")
        
        device = torch.device('cuda')
        model = SimpleNet(input_size=100, hidden_size=64, num_classes=8).to(device)
        optimizer = create_sky_optimizer(model, lr=1e-3)
        criterion = nn.CrossEntropyLoss()
        scaler = GradScaler()
        
        for batch_idx in range(3):
            data = torch.randn(32, 100, device=device)
            target = torch.randint(0, 8, (32,), device=device)
            
            optimizer.zero_grad()
            
            with autocast():
                output = model(data)
                loss = criterion(output, target)
            
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            
            # Validate parameters
            for param in model.parameters():
                assert torch.isfinite(param).all()

    def test_state_dict_compatibility(self):
        """Test state dict save/load across different configurations."""
        model = SimpleNet(input_size=25, hidden_size=32, num_classes=3)
        
        # Train with one configuration
        optimizer1 = create_sky_optimizer(
            model,
            lr=1e-3,
            riemannian_geometry=True,
            natural_gradients=True
        )
        
        # Run a few steps
        for i in range(5):
            data = torch.randn(16, 25)
            target = torch.randint(0, 3, (16,))
            
            optimizer1.zero_grad()
            output = model(data)
            loss = nn.CrossEntropyLoss()(output, target)
            loss.backward()
            optimizer1.step()
        
        # Save state
        state_dict = optimizer1.state_dict()
        
        # Create new optimizer with same configuration and load state
        optimizer2 = create_sky_optimizer(
            model,
            lr=1e-3,
            riemannian_geometry=True,
            natural_gradients=True
        )
        optimizer2.load_state_dict(state_dict)
        
        # Continue training
        data = torch.randn(16, 25)
        target = torch.randint(0, 3, (16,))
        
        optimizer2.zero_grad()
        output = model(data)
        loss = nn.CrossEntropyLoss()(output, target)
        loss.backward()
        optimizer2.step()
        
        # Should work without issues
        for param in model.parameters():
            assert torch.isfinite(param).all()

    @pytest.mark.slow
    def test_convergence_quality(self):
        """Test that Sky Optimizer achieves good convergence on a simple task."""
        # Create a simple regression task
        true_w = torch.randn(10, 1)
        true_b = torch.randn(1)
        
        model = nn.Linear(10, 1)
        optimizer = create_sky_optimizer(
            model,
            lr=1e-2,
            meta_learning=True,
            loss_landscape_aware=True
        )
        criterion = nn.MSELoss()
        
        # Generate training data
        n_samples = 1000
        X = torch.randn(n_samples, 10)
        y = X @ true_w + true_b + 0.1 * torch.randn(n_samples, 1)
        
        # Training loop
        batch_size = 32
        num_epochs = 20
        losses = []
        
        for epoch in range(num_epochs):
            epoch_loss = 0
            num_batches = 0
            
            for i in range(0, n_samples, batch_size):
                batch_X = X[i:i+batch_size]
                batch_y = y[i:i+batch_size]
                
                optimizer.zero_grad()
                pred = model(batch_X)
                loss = criterion(pred, batch_y)
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                num_batches += 1
            
            avg_loss = epoch_loss / num_batches
            losses.append(avg_loss)
        
        # Check that loss decreased significantly
        initial_loss = losses[0]
        final_loss = losses[-1]
        improvement = (initial_loss - final_loss) / initial_loss
        
        print(f"Initial loss: {initial_loss:.6f}")
        print(f"Final loss: {final_loss:.6f}")
        print(f"Improvement: {improvement:.2%}")
        
        # Should achieve at least 80% improvement
        assert improvement > 0.8, f"Insufficient convergence improvement: {improvement:.2%}"
        
        # Check that we learned reasonable parameters
        learned_w = model.weight.data
        learned_b = model.bias.data
        
        # Should be reasonably close to true parameters
        w_error = torch.norm(learned_w.T - true_w) / torch.norm(true_w)
        b_error = torch.abs(learned_b - true_b) / torch.abs(true_b)
        
        print(f"Weight error: {w_error:.3f}")
        print(f"Bias error: {b_error:.3f}")
        
        assert w_error < 0.3, f"Weight learning error too high: {w_error:.3f}"
        assert b_error < 0.3, f"Bias learning error too high: {b_error:.3f}"


if __name__ == "__main__":
    test_suite = TestSkyOptimizerIntegration()
    
    print("Running Sky Optimizer Integration Tests...")
    
    test_suite.test_simple_training_loop()
    print("✓ Simple training loop test passed")
    
    test_suite.test_conv_net_training()
    print("✓ Convolutional network test passed")
    
    test_suite.test_parameter_groups_integration()
    print("✓ Parameter groups test passed")
    
    test_suite.test_state_dict_compatibility()
    print("✓ State dict compatibility test passed")
    
    print("\nAll integration tests passed! ✅")