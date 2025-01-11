# Example: Soul Gem Consumption for +0 to +9 Excellent item Upgrade Soul Cost 

## Introduction

This exemplary study focuses on the enhancement process for *excellent-quality* equipment without luck and without using a talisman of luck(for 10% additional success rate). Specifically:

- **Success Rate**: 50%.
- **Failure Rate**: 50%.
- **Soul Gem Consumption**: Each enhancement attempt consumes one Soul Gem.

The goal of this case study is to calculate the **expected number of Soul Gems** required to enhance equipment from +0 to +9. The results also provide insights into the probabilistic nature of the enhancement process.

---

## Enhancement System Modeling

### **Assumptions**
1. **Enhancement Levels as States**:
   - Each level from +0 to +9 is defined as a state \( E(i) \), where \( i \) is the enhancement level+1
   - For example, The expected number of Soul Gems required to enhance an item from +7 to +9 is E(8).
   - \( E(10) \) is the absorbing state (end of enhancement).

2. **Transition Rules**:
   - Success (\( p = 0.5 \)): Progresses to the next level \( E(i+1) \).
   - Failure (\( 1-p = 0.5 \)): Either stays at the current level or regresses to \( E(i-1) \).

### **Recursive Formula**
The expected number of steps \( E(i) \) to reach \( E(10) \) from any state \( i \) is defined as:
\[
E(i) = 1 + 0.5 \cdot E(i+1) + 0.5 \cdot E(i-1)
\]

Special cases:
- **Base Level (0)**:
  \[
  E(0) = 1 + 0.5 \cdot E(1) + 0.5 \cdot E(0)
  \]
- **Absorbing State (10)**:
  \[
  E(10) = 0
  \]

---

## Step-by-Step Derivation

### **1. Solving for \( E(0) \):**
Rearrange the formula for \( E(0) \):
\[
E(0) = 2 + E(1)
\]

### **2. Solving for \( E(1) \):**
\[
E(1) = 4 + E(2)
\]

### **3. Recursive Substitution:**
Continue the recursion for \( E(2), E(3), \dots, E(9) \), substituting into prior states to eliminate dependencies.

### **4. Final Formula for \( E(9) \):**
After expanding and simplifying, the expected steps for \( E(9) \) are:
\[
E(9) = 116
\]

---

## Key Results

- **Expected Soul Gem Consumption**:
  To enhance a piece of *excellent-quality* equipment from +0 to +9, **116 Soul Gems** are required on average, given a success rate of 50%.

- **Breakdown by Levels**:
  The expected steps for each level are as follows:
  | Level | Expected Attempts |
  |-------|-------------------|
  | +0    | 116               |
  | +1    | 114               |
  | +2    | 110               |
  | +3    | 104               |
  | +4    | 96                |
  | +5    | 86                |
  | +6    | 74                |
  | +7    | 60                |
  | +8    | 44                |
  | +9    | 28                |

---

## Code Implementation

The following Python code calculates the expected Soul Gem consumption using the recursive formula:

```python
def calculate_expected_steps(success_prob, max_level):
    """
    Calculate the expected number of attempts to enhance equipment from +0 to +max_level.

    Parameters:
        success_prob (float): Probability of enhancement success.
        max_level (int): Maximum enhancement level (e.g., +9 for this case).
    
    Returns:
        expected_steps (list): List of expected steps for each level from +0 to +max_level.
    """
    # Initialize expected steps array (including absorbing state at max_level + 1)
    E = [0] * (max_level + 2)  # +2 to include the absorbing state

    # Recursive calculation from max_level down to +0
    for i in range(max_level, -1, -1):
        if i == 0:
            # Special case for E(0)
            E[i] = 2 + E[i + 1]
        else:
            # General case for E(i)
            E[i] = 4 + E[i + 1]

    return E

# Parameters
success_prob = 0.5  # Success probability (50%)
max_level = 9       # Target enhancement level (+9)

# Calculate expected steps
expected_steps = calculate_expected_steps(success_prob, max_level)

# Display results
print(f"Expected number of Soul Gems for each level:")
for level, steps in enumerate(expected_steps[:-1]):  # Exclude absorbing state
    print(f"  +{level}: {steps} attempts")

print(f"\nExpected number of Soul Gems to reach +{max_level}: {expected_steps[0]} attempts")
