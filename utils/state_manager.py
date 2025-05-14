"""
Centralized state management for the SayadGanj Telegram Bot
"""

# Global state dictionary
user_states = {}

def set_user_state(user_id, state):
    """Set a user's state"""
    user_states[user_id] = state
    
def get_user_state(user_id):
    """Get a user's current state"""
    return user_states.get(user_id)
    
def clear_user_state(user_id):
    """Clear a user's state"""
    if user_id in user_states:
        del user_states[user_id]
        
def is_user_in_state(user_id, state_prefix=None):
    """Check if user is in a specific state or state with prefix"""
    if user_id not in user_states:
        return False
        
    if state_prefix:
        return user_states[user_id].startswith(state_prefix)
    
    return True