from cpu.registrador import RegisterFile

regs = RegisterFile()
regs.write(1,123)
print(regs.read(1))
regs.write(0,999)
print(regs.read(0))