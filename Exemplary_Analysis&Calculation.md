# Example: Soul Gem Consumption to Upgrade Excellent item *+0* to *+9* 
#
# This example intends to encourage people to examine my results, to point out what to correct, and to collaborate for further development on this topic. 
# 
## Introduction

This exemplary study focuses on the upgrade process for *excellent-quality* item without luck and without using a talisman of luck ( for 10% additional success rate ). Specifically:

- **Success Rate**: *50%*.
- **Failure Rate**: *50%*.
- **Soul Gem Consumption**: Each enhancement attempt consumes one Soul Gem.

This study aims to calculate the **expected number of Soul Gems** required to enhance equipment from *level +0* to *level +9*. The results also provide insights into the probabilistic nature of the enhancement process.

---

## Upgrade System Modeling

### **Assumptions** 
1. **Item Current Levels as States**:
   - Each level from *level +0* to *+9* is defined as a *state i*, where *state i = current level + 1*, hence *i>=1* , while *"level" >= 0*.
   - For example, a *level +0* item is in *state 1*.
   - The expected number of Souls required to upgrade to *level +9* or *state 10* from *state i* is defined as *E ( i )*
   - For another example, a *level +7* item is in *state 8*, and the expected number of Soul Gems required to enhance this item from *+7* to *+9* is *E( 8 )*.
   - when *state i = 10*, i.e., a *level +9* item, is in the "*absorbing state*" (goal of upgrade), hence *E( 10 ) = 0*;
   - Note: the initial idea of this *"i=lvl+1"* is for **future coding development**, since you can not define state 0 as "No. 0 column in a matrix".  
   
2. **Transition Rules**:
   - Success *p = 0.5*: Progresses to the next level for *state i=1,2,3,4,5,6,7,(lvl +0 to +6)*.
   - Failure *1-p=0.5*:
   -    (1) Stays at the current lvl(state), for *state i=1 or 10---(lvl +0 or +9)*;
   -    (2) Regresses one lvl(state), for *state i=2,3,4,5,6,7---(lvl +1 to +6)*;
   -    (3) Regresses to *state 1---(lvl +0)*, for *state i=8,9---(lvl +7, +8)*;

### **Recursive Formula**
1. **The "Generalized" expected number of Souls E(i) to reach E(10) from any state i is defined as**

      E( i ) = 1 + 0.5 * E( i+1 ) + 0.5 * E( i-1 )

   - 1st term "1" : Represents the one Soul taken during the current attempt, regardless of the outcome.

   - 2nd term "0.5 * E( i+1 )" : If the current process succeeds (with probability 0.5), the system transitions to the next state (i+1). Then the expected Number of Souls is 0.5×E(i+1);
   if this attempt is successful, the remaining required Souls is the expected number of Souls of the next state i+1

2. **Special cases**
   - **Base Level 0 ----------- State i = 1**

        E(1) = 1 + 0.5 * E(2) + 0.5 * E(1)      % fails at lvl 0 stays at lvl 0

   - **Level 7 and 8 ----------- State i = 8 and 9**

        E(i) = 1 + 0.5 * E(i+1) + 0.5 * E(1)      % fails at lvl 7 and 8 regresses to lvl 0
  
   - **Final level 9 ----------- Absorbing State i = 10**:
     
        E(10) = 0    % upgrade goal is achieved.
---

## Step-by-Step Derivation

### **1. Solving for E( 1 )**

Rearrange the formula for E( 1 ):

E(1) = 1 + 0.5 * E(2) + 0.5 * E(1) 

0.5 * E(1) = 0.5 * E(2) + 1

E(1) = E(2) + 2 ---------------------------Eq. 1

### **2. Solving for E( 2 )**

E(2) = 1 + 0.5 * E(3) + 0.5 * E(1)

combine Eq. 1

E(2) = 1 + 0.5 * E(3) + 0.5 * ( E(2) + 2 ) 

E(2) = 1 + 0.5 * E(3) + 0.5 * E(2) + 1 

0.5 * E(2) = 0.5 * E(3) + 2

E(2) = E(3) + 4 ---------------------------Eq. 2

### **3. Solving for E( 3 )**

E(3) = 1 + 0.5 * E(4) + 0.5 * E(2)

Combine Eq.2 

E(3) = 1 + 0.5 * E(4) + 0.5 * ( E(3) + 4 ) 

E(3) = 1 + 0.5 * E(4) + 0.5 * E(3) + 2 

0.5 * E(3) = 0.5 * E(4) + 3

E(3) = E(4) + 6 ---------------------------Eq. 3

### **4. Solving for E( 4 )**

E(4) = 1 + 0.5 * E(5) + 0.5 * E(3)

Combine Eq.3 

E(4) = 1 + 0.5 * E(5) + 0.5 * ( E(3) + 6 ) 

E(4) = 1 + 0.5 * E(5) + 0.5 * E(4) + 3 

0.5 * E(4) = 0.5 * E(5) + 4

E(4) = E(5) + 8 ---------------------------Eq. 4

### **5. Recursive Substitution:**

Continue the recursion for E(5), E(6), E(7),

E(5) = E(6) + 10---------------------------Eq. 5

E(6) = E(7) + 12---------------------------Eq. 6

E(7) = E(8) + 14---------------------------Eq. 7

### **6. Combine Eq.1-7:**

E(1) = E(8) + 2 + 4 + 6 + 8 + 10 + 12 + 14

E(1) = E(8) + 56---------------------------Eq. 8

### **7. Solving for E( 8 )**

E(8) = 1 + 0.5 * E(9) + 0.5 * E(1)

Combine Eq.8

E(8) = 1 + 0.5 * E(9) + 0.5 * ( E(8) + 56 ) 

E(8) = 1 + 0.5 * E(9) + 0.5 * E(8) + 28

0.5 * E(8) = 0.5 * E(9) + 29

E(8) = E(9) + 58---------------------------Eq. 9

### **8. Solving for E( 9 )**

E(9) = 1 + 0.5 * E(10) + 0.5 * E(1)

Combine Eq.8 and E(10) = 0

E(9) = 1 + 0.5 * ( E(8) + 56 ) 

Combine Eq.9

E(9) = 1 + 0.5 * ( E(9) + 58 + 56 ) 

E(9) = 1 + 0.5 * ( E(9) + 114 ) 

E(9) = 1 + 0.5 * E(9) + 57

0.5 * E(9) = 58

E(9) = 116      ---------------------------Eq. 10

### **9. Back to Solving for E( 8 ) - E( 1 )  **

E(8) = E(9) + 58 = 116 + 58 = 174
E(8) = 116 + 58 = 174

E(7) = 188

E(6) = 200

E(5) = 210

E(4) = 218

E(3) = 224

E(2) = 228

E(1) = 230



## Key Results

- **Expected Soul Gem Consumption**:
  To upgrade a piece of *excellent-quality* item from +0 to +9, **230 Soul Gems** are required on "average".

- **Breakdown by Levels**:
  The expected Souls for each level to +9 are as follows:
  | Level       | Expected Souls    |
  |-------------|-------------------|
  | +0 to +9    | 230               |
  | +1 to +9    | 228               |
  | +2 to +9    | 224               |
  | +3 to +9    | 218               |
  | +4 to +9    | 210               |
  | +5 to +9    | 200               |
  | +6 to +9    | 188               |
  | +7 to +9    | 174               |
  | +8 to +9    | 116               |
  | +9 to +9    | 0                 |

---

