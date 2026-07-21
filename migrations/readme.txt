**PERMISSIONS BITFIELD FOR R. SHARP**
note: The server owner possesses all of these at all times. The server owner cannot
      bar themselves from these permissions.

Update 7/12/26: Add Xp management bit
Update 7/21/26: Add Disable command and builtin bit, making the entire length a byte
(toggled on for presentation):

1 1 1 1 1 1 1 1
_ _ _ _ _ _ _ _
| | | | | | | | 
| | | | | | | | 
| | | | | | | | 
| | | | | | | | 
| | | | | | | |-------------------------------------> Grant builtin permissions permission
| | | | | | |----------------------------------> Disable command permission
| | | | | |--------------------------------> Xp management permission
| | | | |-----------------------------> Mute permission
| | | |---------------------> Permission grant permission
| | |--------------------------> Hackban permission
| ---------> Blacklist permission
|----> Manage gemboard permission