## Yet to be a completed Gameboy emulator, written in pure Python
Current state:
* A fully functional CPU.
* A basic implementation of the GPU.

The reason why the project is suspended for now is because of slow nature of Python that make it impossible to progress as were getting 4 fps. The solution will be to rewrite some pare of the emulator as C python extension so they will be executed faster.

![image](https://github.com/user-attachments/assets/a228c0f1-80ed-49c3-a218-2d0f299cd957)

## Resources:
* https://rgbds.gbdev.io/docs/v0.8.0/gbz80.7#LD_r8,r8
* https://www.pastraiser.com/cpu/gameboy/gameboy_opcodes.html
* https://gbdev.io/pandocs/CPU_Instruction_Set.html
* https://gekkio.fi/files/gb-docs/gbctr.pdf
* https://github.com/rockytriton/LLD_gbemu/
* https://github.com/Hacktix/GBEDG/blob/master/ppu/index.md
