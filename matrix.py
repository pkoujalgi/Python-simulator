# largest.py -- Works with largest.txt
# -- Determines largest number in array of 5 numbers
# -- Requires 2 nops after every branch instruction
# -- Improvement - Yet to be IMPLEMENTED -- Need to flush pipeline upon branch taken
# coding: utf-8

# In[7]:


regs = [[0, 0, "$zero", "constant zero"],
        [1, 0, "$at", "assembler temporary"],
        [2, 0, "$v0", "value for function results"],
        [3, 0, "$v1", "value for function results"],
        [4, 0, "$a0", "arguments"],
        [5, 0, "$a1", "arguments"],
        [6, 0, "$a2", "arguments"],
        [7, 0, "$a3", "arguments"],
        [8, 0, "$t0", "temporaries"],
        [9, 0, "$t1", "temporaries"],
        [10, 0, "$t2", "temporaries"],
        [11, 0, "$t3", "temporaries"],
        [12, 0, "$t4", "temporaries"],
        [13, 0, "$t5", "temporaries"],
        [14, 0, "$t6", "temporaries"],
        [15, 0, "$t7", "temporaries"],
        [16, 0, "$s0", "saved temporaries"],
        [17, 0, "$s1", "saved temporaries"],
        [18, 0, "$s2", "saved temporaries"],
        [19, 0, "$s3", "saved temporaries"],
        [20, 0, "$s4", "saved temporaries"],
        [21, 0, "$s5", "saved temporaries"],
        [22, 0, "$s6", "saved temporaries"],
        [23, 0, "$s7", "saved temporaries"],
        [24, 0, "$t8", "temporaries"],
        [25, 0, "$t9", "temporaries"],
        [26, 0, "$k0", "reserved for OS kernel"],
        [27, 0, "$k1", "reserved for OS kernel"],
        [28, 0, "$gp", "global pointer"],
        [29, 0, "$sp", "stack pointer"],
        [30, 0, "$fp", "frame pointer"],
        [31, 0, "$ra", "return address"]]

lo_reg = 0


def display_regs():
    for i in range(8):
        with open("mips_log.txt", 'w') as f:
            print(regs[i * 4][2] + "=", "%#010x" % (regs[i * 4][1]), "    " +
                  regs[i * 4 + 1][2] + "=", "%#010x" % (regs[i * 4 + 1][1]), "    " +
                  regs[i * 4 + 2][2] + "=", "%#010x" % (regs[i * 4 + 2][1]), "    " +
                  regs[i * 4 + 3][2] + "=", "%#010x" % (regs[i * 4 + 3][1]), "    ", file=f
                  )
    return


# ---- CONTROL FIELDS ----
# From Page 266 - Figure 4.18
# key = opcode
# RegDst -- Destination Register selection based upon R or I Format
# ALUSrc -- ALU operand from either register file or sign extended immediate
# MemtoReg -- Loads - selects register write data from memory
# RegWrite -- Write Enable for Register File
# MemRead -- Read Enable for Data Memory
# MemWrite -- Write Enable for Data Memory
# BranchOp -- Branch instruction Operation based on type of branch
# ALUOp -- ALU operation predecode
# | RegDst | ALUSrc | MemtoReg | RegWrite | MemRead | MemWrite | Branch | ALUOp |
control = {0b000000: [1, 0, 0, 1, 0, 0, 0, 2],  # R Format
           0b100011: [0, 1, 1, 1, 1, 0, 0, 0],  # lw
           0b101011: [0, 1, 0, 0, 0, 1, 0, 0],  # sw
           0b000100: [0, 0, 0, 0, 0, 0, 1, 1],  # beq
           0b000001: [0, 0, 0, 0, 0, 0, 2, 1],  # bgez
           0b001101: [0, 1, 0, 1, 0, 0, 0, 3],  # ori
           0b001000: [0, 1, 0, 1, 0, 0, 0, 3]  # addi
           }  # beq

ALU = {0b0000: lambda src1, src2: ["and", src1 & src2, "bitwise and"],
       0b0001: lambda src1, src2: ["or", src1 | src2, "bitwise or"],
       0b0010: lambda src1, src2: ["add", src1 + src2, "add signed"],
       0b0110: lambda src1, src2: ["sub", src1 - src2, "sub signed"],
       0b0111: lambda src1, src2: ["slt", 0, "set on less than"],
       0b1100: lambda src1, src2: ["nor", ~(src1 | src2), "bitwise nor"],
       0b1000: lambda src1, src2: ["mult", src1 * src2, "multiply"],
       0b1001: lambda src1, src2: ["mflo", 0, "mflo dummy"]}

decode_funct = {0b000000: ["or", 0b0001],
                0b100000: ["add", 0b0010],
                0b100010: ["sub", 0b0110],
                0b100100: ["and", 0b0000],
                0b100101: ["or", 0b0001],
                0b101010: ["slt", 0b0111],
                0b011001: ["multu", 0b1000],
                0b010010: ["mflo", 0b1001]}  # dummy AND operation as src1, src2 = $zero

decode_Itype = {0b001101: ["or", 0b0001],
                0b001000: ["add", 0b0010]}


def ALU_control(ALUOp, funct, opcode):
    if (ALUOp == 0):  # lw, sw => add
        return (0b0010)

    if (ALUOp == 1):  # beq => sub
        return (0b0110)
    if (ALUOp == 2):  # Rtype
        return (decode_funct[funct][1])
    if (ALUOp == 3):  # Itype
        return (decode_Itype[opcode][1])


def Branch_control(BranchOp, Zero, Negative):
    BranchFinal = 0  # Default Branch NOT TAKEN
    if (BranchOp == 0):  # No Branch
        BranchFinal = 0

    if (BranchOp == 1):  # Branch =
        if (Zero == 1):
            BranchFinal = 1

    if (BranchOp == 2):  # Branch >=
        if (Zero == 1) or (Negative == 0):
            BranchFinal = 1

    if (BranchOp == 3):  # Branch >
        if (Zero == 0) and (Negative == 0):
            BranchFinal = 1

    if (BranchOp == 4):  # Branch <=
        if (Zero == 1) or (Negative == 1):
            BranchFinal = 1

    if (BranchOp == 5):  # Branch <
        if (Zero == 0) and (Negative == 1):
            BranchFinal = 1

    return (BranchFinal)


# Initialize Memory

inst_mem = []

# matrixA => 0 * 4 = 0
# matrixX => 6 * 4 = 24
# matrixB => 12 * 4 = 48
# sizeA => 16 * 4 = 64
# sizeX => 18 * 4 = 72
# sizeB => 20 * 4 = 80


data_mem = [1,2,  3,4,  # matrixA
            2,4,  # matrixX
            0,0,  # matrixB
            2,2,  # sizeA
            2,1,  # sizeX
            2,1]  # sizeB


def read_instr():
    # infile = open("basic_instructions.txt","r")
    infile = open("instruction.txt", "r")
    lines = infile.readlines()
    codelines = [x for x in lines if x[0] != "#"]
    for line in codelines:
        words = line.split()
        mem = (int(words[0], 16), int(words[1], 16), words[2])
        inst_mem.append(mem)
    infile.close()
    return


read_instr()  # Read Instruction Memory
with open("mips_log.txt", 'w') as f:
    print(inst_mem, file=f)

    # ***** Start of Machine *****
    PC = 0

    s0_valid = 0  # Stage 0 Valid -- Fetch
    s1_valid = 0  # Stage 1 Valid -- Decode
    s2_valid = 0  # Stage 2 Valid -- Execute
    s3_valid = 0  # Stage 3 Valid -- Memory
    s4_valid = 0  # Stage 4 Valid -- Writeback

    # Stage S0 -- fetch -- signals
    instruction = 0
    PC_plus_4 = 0
    instr_S0 = [0, 0, "nop"]

    # Stage S1 -- decode -- signals

    instruction_S1 = 0
    PC_plus_4_S1 = 0
    read_data1 = 0
    read_data2 = 0
    sign_ext = 0
    my_op = 0
    my_rd = 0
    my_rt = 0
    read_register1 = 0
    read_register2 = 0
    my_funct = 0
    control_word_S1 = [0, 0, 0, 0, 0, 0, 0, 0]
    instr_S1 = [0, 0, "nop"]
    BranchOp = 0

    # Stage S2 -- execute -- signals

    PC_plus_4_S2 = 0
    read_data1_S2 = 0
    read_data2_S2 = 0
    sign_ext_S2 = 0
    my_rd_S2 = 0
    my_rt_S2 = 0
    read_register2_S2 = 0
    Zero = 0
    Negative = 0
    alu_result = 0
    my_funct_S2 = 0
    branch_target = 0
    control_word_S2 = [0, 0, 0, 0, 0, 0, 0, 0]
    instr_S2 = [0, 0, "nop"]
    stall = 0

    # Stage S3 -- memory -- signals

    my_rd_S3 = 0
    my_rt_S3 = 0
    read_register2_S3 = 0
    Zero_S3 = 0
    alu_result_S3 = 0
    control_word_S3 = [0, 0, 0, 0, 0, 0, 0, 0]
    instr_S3 = [0, 0, "nop"]

    # Stage S4 -- writeback -- signals

    my_rd_S4 = 0
    my_rt_S4 = 0
    read_register2_S4 = 0
    alu_result_S4 = 0
    memory_read_data = 0
    control_word_S4 = [0, 0, 0, 0, 0, 0, 0, 0]
    instr_S4 = [0, 0, "nop"]

    for cycle in range(29):
        print("***********************************************************************", file=f)
        print("Cycle = ", cycle, file=f)

        # Update States
        s4_valid = s3_valid
        s3_valid = s2_valid
        s2_valid = s1_valid
        s1_valid = s0_valid

        instr_S4 = instr_S3
        instr_S3 = instr_S2

        if stall == 0:
            instr_S2 = instr_S1
            instr_S1 = instr_S0
        else:
            instr_S2 = [0, 0, "nop"]

        if stall == 0:
            instruction_S1 = instruction
            PC_plus_4_S2 = PC_plus_4_S1
            PC_plus_4_S1 = PC_plus_4

        if stall == 0:
            read_data1_S2 = read_data1
        else:
            read_data1_S2 = 0

        read_data2_S3 = read_data2_S2

        if stall == 0:
            read_data2_S2 = read_data2
        else:
            read_data2_S2 = 0

        if stall == 0:
            sign_ext_S2 = sign_ext
            my_funct_S2 = my_funct
            my_op_S2 = my_op
        else:
            my_funct_S2 = 0
            sign_ext_S2 = 0

        read_register2_S4 = read_register2_S3
        read_register2_S3 = read_register2_S2

        if stall == 0:
            read_register2_S2 = read_register2
        else:
            read_register2_S2 = 0

        if stall == 0:
            read_register1_S2 = read_register1
        else:
            read_register1_S2 = 0

        my_rd_S4 = my_rd_S3
        my_rd_S3 = my_rd_S2

        if stall == 0:
            my_rd_S2 = my_rd
        else:
            my_rd_S2 = 0

        if stall == 0:
            BranchOp_S2 = BranchOp
        else:
            BranchOp = 0

        Zero_S3 = Zero

        alu_result_S4 = alu_result_S3
        alu_result_S3 = alu_result

        branch_target_S3 = branch_target

        memory_read_data_S4 = memory_read_data

        control_word_S4 = control_word_S3
        control_word_S3 = control_word_S2
        if stall == 0:
            control_word_S2 = control_word_S1
        else:
            control_word_S2 = [0, 0, 0, 0, 0, 0, 0, 0]

        # Stage S0 -- fetch instruction
        print("S0 -- PC = ", "%#010x" % (PC), file=f)
        print("S0 -- PC>>2 = ", "%#010x" % (PC >> 2), file=f)
        instr_S0 = inst_mem[PC >> 2]
        addr = inst_mem[PC >> 2][0]
        instruction = inst_mem[PC >> 2][1]
        assembly = inst_mem[PC >> 2][2]
        # print("Fetch -- S0: valid", s0_valid, "%#010x"% (addr), "%#010x"% (instruction), assembly)
        print("Fetch -- S0: valid", s0_valid, "%#010x" % (instr_S0[0]), "%#010x" % (instr_S0[1]), instr_S0[2], file=f)

        s0_valid = 1

        # Stage S1 -- decode instruction
        print("Decode -- S1: valid", s1_valid, "%#010x" % (instr_S1[0]), "%#010x" % (instr_S1[1]), instr_S1[2], file=f)

        my_op = instruction_S1 >> 26
        my_rs = (instruction_S1 >> 21) & 0x1F
        my_rt = (instruction_S1 >> 16) & 0x1F
        my_rd = (instruction_S1 >> 11) & 0x1F
        my_shamt = (instruction_S1 >> 6) & 0x1F
        my_funct = instruction_S1 & 0x3F
        my_imm = instruction_S1 & 0xFFFF

        # register file sources
        read_register1 = my_rs
        read_register2 = my_rt

        #### Register  Writes in 1st Half of Cycle  -- BEGIN --
        MemtoReg_S4 = control_word_S4[2]
        RegDst_S4 = control_word_S4[0]
        RegWrite_S4 = control_word_S4[3]

        # register write back
        register_write_data = memory_read_data_S4 if MemtoReg_S4 else alu_result_S4
        # write_register = my_rd if RegDst else my_rt
        write_register = my_rd_S4 if RegDst_S4 else read_register2_S4

        if s4_valid == 1:
            if RegWrite_S4:
                if write_register != 0:
                    regs[write_register][1] = register_write_data
                    #### Register  Writes in 1st Half of Cycle  -- BEGIN --

        # register file data
        read_data1 = regs[read_register1][1]
        read_data2 = regs[read_register2][1]

        # sign extension of immediate data
        sign_bit = (my_imm >> 15) & 0x1
        sign_ext = (0xffff0000 | my_imm) if (sign_bit == 1) else my_imm

        if s1_valid == 1:
            # control signals
            control_word_S1 = control[my_op]
        else:
            control_word_S1 = [0, 0, 0, 0, 0, 0, 0, 0]

        RegDst = control_word_S1[0]
        ALUSrc = control_word_S1[1]
        MemtoReg = control_word_S1[2]
        RegWrite = control_word_S1[3]
        MemRead = control_word_S1[4]
        MemWrite = control_word_S1[5]
        BranchOp = control_word_S1[6]
        ALUOp = control_word_S1[7]

        # Stage S2 - Execute
        print("Execute -- S2: valid", s2_valid, "%#010x" % (instr_S2[0]), "%#010x" % (instr_S2[1]), instr_S2[2], file=f)

        ALUSrc_S2 = control_word_S2[1]
        ALUOp_S2 = control_word_S2[7]

        # alu sources
        alu_src1 = read_data1_S2
        # alu_src2_mux1 = sign_ext_S2 if ALUSrc_S2 else read_data2_S2

        # Load - Data Hazard Detection and Stall Generation
        # ************************************************
        if (((s2_valid == 1) and (s1_valid == 1) and (control_word_S2[4] == 1)) and
                ((read_register2_S2 == read_register1) or
                     (read_register2_S2 == read_register2))
            ):
            stall = 1
        else:
            stall = 0

        print("S2 -- stall = ", stall, file=f)

        # Data Hazard Detection
        # ************************************************
        # Forwarding Unit - rs
        if (((control_word_S3[3] == 1) and
                 (my_rd_S3 != 0) and
                 (my_rd_S3 == read_register1_S2)) or
                ((control_word_S3[0] == 0) and
                     (control_word_S3[3] == 1) and
                     (read_register2_S3 != 0) and
                     (read_register2_S3 == read_register1_S2))
            ):
            ForwardA = 2
        elif (((control_word_S4[3] == 1) and
                   (my_rd_S4 != 0) and
                   (my_rd_S4 == read_register1_S2)) or
                  ((control_word_S4[0] == 0) and
                       (control_word_S4[3] == 1) and
                       (read_register2_S4 != 0) and
                       (read_register2_S4 == read_register1_S2))
              ):
            ForwardA = 1
        else:
            ForwardA = 0

        # Forwarding Unit - rt
        if (((control_word_S3[3] == 1) and
                 (my_rd_S3 != 0) and
                 (my_rd_S3 == read_register2_S2)) or
                ((control_word_S3[0] == 0) and
                     (control_word_S3[3] == 1) and
                     (read_register2_S3 != 0) and
                     (read_register2_S3 == read_register2_S2))
            ):
            ForwardB = 2
        elif (((control_word_S4[3] == 1) and
                   (my_rd_S4 != 0) and
                   (my_rd_S4 == read_register2_S2)) or
                  ((control_word_S4[0] == 0) and
                       (control_word_S4[3] == 1) and
                       (read_register2_S4 != 0) and
                       (read_register2_S4 == read_register2_S2))
              ):
            ForwardB = 1
        else:
            ForwardB = 0

        # ForwardA
        if ForwardA == 0:
            alu_src1 = read_data1_S2
        elif ForwardA == 1:
            alu_src1 = memory_read_data_S4 if MemtoReg_S4 else alu_result_S4
        elif ForwardA == 2:
            alu_src1 = alu_result_S3
        else:
            alu_src1 = 0  # Should Never OCCUR

        # ForwardB
        if ForwardB == 0:
            alu_src2_FB = read_data2_S2
        elif ForwardB == 1:
            alu_src2_FB = memory_read_data_S4 if MemtoReg_S4 else alu_result_S4
        elif ForwardB == 2:
            alu_src2_FB = alu_result_S3
        else:
            alu_src2_FB = 0  # Should Never OCCUR

        alu_src2 = sign_ext_S2 if ALUSrc_S2 else alu_src2_FB

        print("S2 - ForwardA = ", ForwardA, " ForwardB = ", ForwardB, file=f)
        print("my_rs = ", read_register1_S2, " my_rt = ", read_register2_S2, file=f)
        print("alu_src1 = ", "%#010x" % (alu_src1), "alu_src2 = ", "%#010x" % (alu_src2), file=f)
        print("alu_src2_FB = ", "%#010x" % (alu_src2_FB), "sign_ext_S2 = ", "%#010x" % (sign_ext_S2), file=f)

        # ************************************************



        if s2_valid == 1:
            alu_operation = ALU_control(ALUOp_S2, my_funct_S2, my_op_S2)
            alu_entry = ALU[alu_operation](alu_src1, alu_src2)
            alu_result = alu_entry[1]
            Zero = 1 if (alu_result == 0) else 0
            Negative = 1 if (alu_result < 0) else 0

            if alu_operation == 8:
                lo_reg = alu_result
                print("multiply -- lo_reg = ", lo_reg, file=f)

            if alu_operation == 9:
                alu_result = lo_reg
                print("mflo", file=f)  # does not set Zero and Negative Flags

        print("BranchOp_S2 = ", BranchOp_S2, Zero, Negative, file=f)
        if s2_valid == 1:
            Branch_S2 = Branch_control(BranchOp_S2, Zero, Negative)
        else:
            Branch_S2 = 0
        print("Branch_S2 = ", Branch_S2, file=f)

        # Stage S3 -- Memory
        print("Memory -- S3: valid", s3_valid, "%#010x" % (instr_S3[0]), "%#010x" % (instr_S3[1]), instr_S3[2], file=f)

        MemRead_S3 = control_word_S3[4]
        MemWrite_S3 = control_word_S3[5]

        # data memory operations
        if s3_valid == 1:
            if MemWrite_S3:
                data_mem[alu_result_S3 >> 2] = read_data2_S3
                print("MemWrite -- addr", alu_result_S3, file=f)
                print("MemWrite -- data", read_data2_S3, file=f)

            if MemRead_S3:
                memory_read_data = data_mem[alu_result_S3 >> 2]

        # Stage S4 -- Write back
        print("WriteBack -- S4: valid", s4_valid, "%#010x" % (instr_S4[0]), "%#010x" % (instr_S4[1]), instr_S4[2],
              file=f)

        #### Moved to Decode Stage to emulate Register Write on 1st Half of Cycle -- BEGIN --
        #    MemtoReg_S4 = control_word_S4[2]
        #    RegDst_S4 = control_word_S4[0]
        #    RegWrite_S4 = control_word_S4[3]
        #
        #    #register write back
        #    register_write_data = memory_read_data_S4 if MemtoReg_S4 else alu_result_S4
        #    #write_register = my_rd if RegDst else my_rt
        #    write_register = my_rd_S4 if RegDst_S4 else read_register2_S4
        #
        #    if s4_valid == 1:
        #        if RegWrite_S4:
        #            regs[write_register][1] = register_write_data
        #### Moved to Decode Stage to emulate Register Write on 1st Half of Cycle -- BEGIN --

        # ---- Next PC Calculation ----
        if stall == 0:
            PC_plus_4 = PC + 4

        branch_target = (PC_plus_4_S2 + ((sign_ext_S2 << 2) & 0xffffffff)) & 0xffffffff

        print("branch_target = ", "%#010x" % (branch_target), file=f)

        pc_mux1 = branch_target if (Branch_S2 == 1) else PC_plus_4
        Jump = 0
        pc_mux2 = 0 if (Jump) else pc_mux1

        PC = pc_mux2  # Next Instruction

        # ---- Dump Registers After Instruction ----
        display_regs()

        print("alu_result_S4", alu_result_S4, file=f)
        print("alu_result_S3", alu_result_S3, file=f)
        print("alu_result", alu_result, file=f)

        # -- End of Main Loop








