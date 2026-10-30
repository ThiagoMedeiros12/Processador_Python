from cpu.alu import clz32 

casos = [
    (0x00000000,32),
    (0x00000001,31),
    (0x00000002,30),
    (0x00000008,28),
    (0x80000000,0),
    (0xFFFFFFFF,0)
]

for entrada, esperado in casos: 
    obtido = clz32(entrada)
    print(hex(entrada),obtido,"esperado:",esperado)
    assert obtido == esperado