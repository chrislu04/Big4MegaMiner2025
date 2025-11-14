import os
import time
import torch
import argparse
from pathlib import Path
import supersuit as ss
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, EvalCallback, CallbackList
from stable_baselines3.common.vec_env import VecMonitor
from pettingzoo.utils.conversions import aec_to_parallel

# Add the backend directory to the Python path if it's not already
try:
    import MegaMinerEnv
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from AI_Agents import MegaMinerEnv

class TimeLimitCallback(BaseCallback):
    """
    A custom callback that stops training after a specified time limit.
    """
    def __init__(self, max_time: int, verbose: int = 0):
        super(TimeLimitCallback, self).__init__(verbose)
        self.start_time = time.time()
        self.max_time = max_time

    def _on_step(self) -> bool:
        """
        This method will be called by the model after each call to `env.step()`.
        :return: (bool) If the callback returns False, training is aborted early.
        """
        elapsed_time = time.time() - self.start_time
        if elapsed_time > self.max_time:
            if self.verbose > 0:
                print(f"Stopping training as time limit of {self.max_time} seconds reached.")
            return False
        return True

def main(args):
    """
    Main function to set up and run the PPO training.
    """
    # --- 0. Configure Logging ---
    if args.enable_logging:
        os.environ["MEGAMINER_LOGGING"] = "ON"
    
    # --- 1. Set Device ---
    if torch.backends.mps.is_available():
        device = "mps"
        print("Using MPS (Apple Silicon GPU) for training.")
    else:
        device = "cpu"
        print("MPS not available, using CPU for training.")

    # --- 2. Setup Environment ---
    map_file = str(Path(__file__).resolve().parent.parent / 'maps' / args.map_path)
    env = MegaMinerEnv.env(map_path=map_file)
    env = aec_to_parallel(env)

    # --- 3. Wrap Environment for SB3 ---
    env = ss.pettingzoo_env_to_vec_env_v1(env)
    env = ss.concat_vec_envs_v1(env, num_vec_envs=1, num_cpus=1, base_class="stable_baselines3")
    
    # --- 4. Setup PPO Model ---
    log_dir = "training/logs/"
    os.makedirs(log_dir, exist_ok=True)
    model_dir = "training/models/"
    os.makedirs(model_dir, exist_ok=True)
    
    best_model_path = os.path.join(model_dir, "best_model", "best_model.zip")

    if os.path.exists(best_model_path):
        print("--- Loading existing model and continuing training ---")
        model = PPO.load(best_model_path, env=env, tensorboard_log=log_dir, device=device)
        # Reset the logger to continue logging without resetting timesteps
        from stable_baselines3.common import utils
        model.set_logger(utils.configure_logger(verbose=1, tensorboard_log=log_dir, reset_num_timesteps=False))
    else:
        print("--- No existing model found, starting new training ---")
        model = PPO(
            "MlpPolicy", # Use MlpPolicy
            env,
            verbose=1,
            tensorboard_log=log_dir,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            ent_coef=0.01,
            device=device,  # Use the selected device (mps or cpu)
        )

    # --- 5. Setup Callbacks ---
    # Time limit callback
    max_training_time_seconds = args.train_minutes * 60
    time_callback = TimeLimitCallback(max_time=max_training_time_seconds, verbose=1)

    # Evaluation callback
    eval_env = MegaMinerEnv.env(map_path=map_file)
    eval_env = aec_to_parallel(eval_env)
    eval_env = ss.pettingzoo_env_to_vec_env_v1(eval_env)
    eval_env = ss.concat_vec_envs_v1(eval_env, num_vec_envs=1, num_cpus=1, base_class="stable_baselines3")

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=os.path.join(model_dir, "best_model"),
        log_path=f"{log_dir}/eval",
        eval_freq=10000,
        deterministic=True,
        render=False
    )
    
    # Combine callbacks
    callback_list = CallbackList([eval_callback, time_callback])

    # --- 6. Train the Model ---
    # Set total_timesteps to a very large number so that training is stopped by the time limit callback.
    print(f"--- Starting PPO Training for {args.train_minutes} minutes ---")
    model.learn(total_timesteps=10_000_000, callback=callback_list)
    print("--- Finished Training ---")

    # --- 7. Save the Final Model ---
    final_model_path = f"{model_dir}/ppo_megaminer_final"
    model.save(final_model_path)
    print(f"Final model saved to {final_model_path}")
    print(f"Best performing model saved in {model_dir}/best_model/")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--enable-logging", action="store_true", help="Enable game engine logging during training.")
    parser.add_argument("--map-path", type=str, default="test_map.json", help="Specify the map file to use for training (e.g., 'test_map.json').")
    parser.add_argument("--train-minutes", type=int, default=20, help="Specify the number of minutes to train the PPO agent.")
    args = parser.parse_args()
    main(args)
