# Inference Script Alignment with Environment.py

## Configuration
- `API_KEY`: Reads from `GROQ_API_KEY` environment variable
- `MODEL_NAME`: Reads from `MODEL_NAME` env var, defaults to `llama-3.1-8b-instant`
- `MAX_STEPS_PER_TASK`: 25 steps per task

## Task Flow

### 1. Reset (per task: easy, medium, hard)
```python
result = env.reset(task=task)
obs = result.observation
reward = result.reward or 0.0
```
- Defaults to first task of difficulty (easy_1_checkout, medium_1_modal, hard_1_cart)
- Returns A11yObservation with discovery bonus applied

### 2. Step Execution Loop
```python
action = A11yAction(**{k: v for k, v in action_json.items() if k != "thought"})
result = env.step(action)
```
- Accepts: `action_type`, `element_id`, `attribute`, `value`
- Returns A11yObservation with updated reward

### 3. Reward Tracking
- **Discovery Phase**: +0.2 bonus when issue found (via SCREEN_READER)
- **Fix Phase**: Gradual increase toward 1.0 as fixes applied
- **Grouping Support**: Completes any fix in group = group completed

## Actions Supported

| Action Type | Parameters | Example |
|---|---|---|
| SCREEN_READER | element_id | `{"action_type": "SCREEN_READER", "element_id": "checkout-btn"}` |
| TAB | none | `{"action_type": "TAB"}` |
| MODIFY | element_id, attribute, value | `{"action_type": "MODIFY", "element_id": "btn", "attribute": "aria-label", "value": "Submit"}` |
| CLICK | element_id | `{"action_type": "CLICK", "element_id": "add-btn"}` |

## Observations Provided

Each A11yObservation includes:
- `message`: Action result (e.g., "Screen Reader says: 'Unlabelled element...'", "[ISSUE FOUND! +0.2 discovery reward]")
- `dom_snapshot`: Current DOM state
- `focus_order`: Tab order for TAB action
- `reward`: Current score (discovery bonus + fixes)
- `done`: Whether task complete

## Logging Format 

```
[START] task=easy env=openenv model=llama-3.1-8b-instant
[STEP] step=1 action=screen_reader(checkout-btn) reward=0.20 done=false error=null
[STEP] step=2 action=modify(checkout-btn,aria-label,Checkout) reward=0.50 done=false error=null
...
[END] success=true steps=5 score=1.00 rewards=0.20,0.50,0.70,0.90,1.00
```

## Key Features Aligned 

✅ Discovery bonus (0.2) only awarded when base_score is 0  
✅ Grouping/weight logic for partial progress  
✅ Supports 4 action types (SCREEN_READER, TAB, MODIFY, CLICK)  
✅ Rich reward feedback in observations  
✅ Proper error handling and fallback to TAB  
✅ Rate limit handling for Groq API  
✅ Three difficulty levels (easy, medium, hard)  
✅ Reproducible baseline scoring

## Usage

```bash
export GROQ_API_KEY="gsk-..."
python inference.py
```

The script will run all 3 tasks and output baseline scores to stdout (structured logs) and stderr (summary).
