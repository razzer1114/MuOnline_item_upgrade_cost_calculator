# Simple Case: Expected Soul Gems from +0 to +2 [中文](Simple_Case_CN.md)

This simple case shows the basic idea of expectation calculation using only three states.

## Problem

Calculate:

> The expected number of Soul Gems required to reach +2 from +0.

## Assumptions

- Success probability:

$$
p = 0.5
$$

- Failure probability:

$$
1-p = 0.5
$$

- Each upgrade attempt consumes **1 Soul Gem**.

## Transition Rules

From +0:

- Success: +0 → +1
- Failure: stays at +0

From +1:

- Success: +1 → +2
- Failure: drops back to +0




## State Definition

| State | Item Level |
|---|---|
| 1 | +0 |
| 2 | +1 |
| 3 | +2 |




## Recursive Equations

Let:

$$
E(i)=\text{expected number of Soul Gems required to reach +2 from state } i
$$

State 3 (Level +2) is the target State (Level), no more gem is needed, hence the expected gem to reach target level from State 3 is 0, duh:

$$
E(3)=0
$$

For state 1, $E(i)$ consists of: 

- 1 : you need 1 gem to do the attempt no matter what the outcome is;

- 0.5 * $E(2)$: when the attempt is successful, the item reaches Level +1 as in State 2, for p=0.5 chance;

- 0.5 * $E(1)$: when the attempt is unsuccessful，the item stays at Level +0 as in State 1, for p=0.5 chance:

So $E(i)$ is represented as:

$$
E(1)=1+0.5E(2)+0.5E(1)
$$

Rearrange:

$$
0.5E(1)=1+0.5E(2)
$$

$$
E(1)=E(2)+2
$$

For state 2:

$$
E(2)=1+0.5E(3)+0.5E(1)
$$

Since:

$$
E(3)=0
$$

we have:

$$
E(2)=1+0.5E(1)
$$

Substitute:

$$
E(1)=E(2)+2
$$

into the equation:

$$
E(2)=1+0.5(E(2)+2)
$$

$$
E(2)=1+0.5E(2)+1
$$

$$
0.5E(2)=2
$$

$$
E(2)=4
$$

Then:

$$
E(1)=E(2)+2=6
$$

## Final Result

| Start Level | Expected Soul Gems to +2 |
|---|---:|
| +0 | 6 |
| +1 | 4 |
| +2 | 0 |

Therefore:

$$
\boxed{E(+0 \rightarrow +2)=6}
$$

## Key Idea

Even though only two successful upgrades are needed, failures increase the expected cost because:

- failure at +0 consumes one Soul Gem but keeps the item at +0;
- failure at +1 consumes one Soul Gem and returns the item to +0.
