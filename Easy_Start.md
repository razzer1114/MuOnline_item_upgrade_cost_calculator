# Simple start
### success rate p=q=0.5 with only Souls
## lvl 0 to 1 === State 1 to 2

E ( 2 ) = 0

E ( 1 ) = 1 + 0.5 * E ( 2 ) + 0.5 * E ( 1 )
  - 0.5 * E ( 1 ) = 0.5 * E ( 2 ) + 1
  - E ( 1 ) = E ( 2 ) + 2
  - E ( 1 ) =    2 

### Upgrade a level 0 item to level 1 needs Souls
#
#
## lvl 0 to 2 === State 1 to 3
E ( 3 ) = ---------------------------------------------Eq.1

E ( 1 ) = 1 + 0.5 * E ( 2 ) + 0.5 * E ( 1 )
  - 0.5 * E ( 1 ) = 0.5 * E ( 2 ) + 1
  - E ( 1 ) = E ( 2 ) + 2 -------------------------------Eq.2

E ( 2 ) = 1 + 0.5 * E ( 3 ) + 0.5 * E ( 1 )
  - combine Eq.2
  - E ( 2 ) = 1 + 0.5 * E ( 3 ) + 0.5 * ( E ( 2 ) + 2 )
  - E ( 2 ) = 1 + 0.5 * E ( 3 ) + 0.5 * E ( 2 ) + 1
  - 0.5 * E ( 2 ) = 1 + 0.5 * E ( 3 ) + 1
  - E ( 2 ) = E ( 3 ) + 4
  - combine Eq.1
  - E ( 2 ) =    0  + 4
  - E ( 2 ) =    4

E ( 1 ) =  E ( 2 ) + 2
  - E ( 1 ) =  4 ＋ 2 = 6
### Upgrade a level 0 item to level 2 needs 6 Souls


