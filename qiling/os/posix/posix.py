#!/usr/bin/env python3
# 
# Cross Platform and Multi Architecture Advanced Binary Emulation Framework
# Built on top of Unicorn emulator (www.unicorn-engine.org) 

# For syscall_num
from unicorn.arm64_const import *
from unicorn.arm_const import *
from unicorn.mips_const import *
from unicorn.x86_const import *

from qiling.const import *
from qiling.os.os import QlOs
from qiling.utils import *
from qiling.exception import *

from qiling.os.posix.syscall import *
from qiling.os.linux.syscall import *
from qiling.os.macos.syscall import *
from qiling.os.freebsd.syscall import *


class QlOsPosix(QlOs):
    def __init__(self, ql):
        super(QlOsPosix, self).__init__(ql)
        self.ql = ql
        self.sigaction_act = []

        self.file_des = []
        self.dict_posix_syscall = dict()
        self.dict_posix_syscall_by_num = dict()
        
        self.syscall_map = None
        self.syscall_name = None

        if self.ql.ostype in QL_POSIX:
            self.file_des = [0] * 256
            self.file_des[0] = self.stdin
            self.file_des[1] = self.stdout
            self.file_des[2] = self.stderr

        for _ in range(256):
            self.sigaction_act.append(0)
        
    # ql.syscall - get syscall for all posix series
    @property
    def syscall(self):
        return self.get_syscall()


    # ql.syscall_param - get syscall for all posix series
    @property
    def syscall_param(self):
        return self.get_syscall_param()


    def load_syscall(self, intno = None):
        map_syscall = self.ql.os_setup(function_name = "map_syscall")
        param0 , param1, param2, param3, param4, param5 = self.syscall_param
        self.syscall_map = self.dict_posix_syscall_by_num.get(self.syscall)
        
        if self.syscall_map != None:
            self.syscall_name = self.syscall_map.__name__
        else:
            self.syscall_name = map_syscall(self.syscall)
            if self.syscall_name != None:
                replace_func = self.dict_posix_syscall.get(self.syscall_name)
                if replace_func != None:
                    self.syscall_map = replace_func
                    self.syscall_name = replace_func.__name__
                else:
                    self.syscall_map = eval(self.syscall_name)
            else:
                self.syscall_map = None
                self.syscall_name = None

        if self.syscall_map != None:
            try:
                self.syscall_map(self.ql, param0, param1, param2, param3, param4, param5)
            except KeyboardInterrupt:
                raise            
            except Exception as e:
                self.ql.nprint("[!] Syscall ERROR: %s DEBUG: %s" % (self.syscall_name, e))
                raise
        else:
            self.ql.nprint("[!] 0x%x: syscall number = 0x%x(%d) not implemented" %(self.ql.reg.pc, self.syscall, self.syscall))
            if self.ql.debug_stop:
                raise QlErrorSyscallNotFound("[!] Syscall Not Found")

    # get syscall
    def get_syscall(self):
        if self.ql.archtype== QL_ARCH.ARM64:
            if self.ql.ostype == QL_OS.MACOS:
                syscall_num = UC_ARM64_REG_X16
            else:
                syscall_num = UC_ARM64_REG_X8
        elif self.ql.archtype== QL_ARCH.ARM:
            syscall_num = UC_ARM_REG_R7
        elif self.ql.archtype== QL_ARCH.MIPS32:
            syscall_num = UC_MIPS_REG_V0        
        elif self.ql.archtype== QL_ARCH.X86:
            syscall_num = UC_X86_REG_EAX
        elif self.ql.archtype== QL_ARCH.X8664:
            syscall_num = UC_X86_REG_RAX           

        return self.ql.register(syscall_num)

    def definesyscall_return(self, regreturn):
        if (self.ql.archtype== QL_ARCH.ARM):  # ARM
            self.ql.register(UC_ARM_REG_R0, regreturn)
            # ql.nprint("-[+] Write %i to UC_ARM_REG_R0" % regreturn)

        elif (self.ql.archtype== QL_ARCH.ARM64):  # ARM64
            self.ql.register(UC_ARM64_REG_X0, regreturn)

        elif (self.ql.archtype== QL_ARCH.X86):  # X86
            self.ql.register(UC_X86_REG_EAX, regreturn)

        elif (self.ql.archtype== QL_ARCH.X8664):  # X8664
            self.ql.register(UC_X86_REG_RAX, regreturn)

        elif (self.ql.archtype== QL_ARCH.MIPS32):  # MIPSE32EL
            if regreturn < 0 and regreturn > -1134:
                a3return = 1
                regreturn = - regreturn
            else:
                a3return = 0
            # if ql.output == QL_OUTPUT.DEBUG:
            #    print("[+] A3 is %d" % a3return)
            self.ql.register(UC_MIPS_REG_V0, regreturn)
            self.ql.register(UC_MIPS_REG_A3, a3return)

    # get syscall
    def get_syscall_param(self):
        if self.ql.archtype== QL_ARCH.ARM64:
            param0 = self.ql.register(UC_ARM64_REG_X0)
            param1 = self.ql.register(UC_ARM64_REG_X1)
            param2 = self.ql.register(UC_ARM64_REG_X2)
            param3 = self.ql.register(UC_ARM64_REG_X3)
            param4 = self.ql.register(UC_ARM64_REG_X4)
            param5 = self.ql.register(UC_ARM64_REG_X5)
        elif self.ql.archtype== QL_ARCH.ARM:
            param0 = self.ql.register(UC_ARM_REG_R0)
            param1 = self.ql.register(UC_ARM_REG_R1)
            param2 = self.ql.register(UC_ARM_REG_R2)
            param3 = self.ql.register(UC_ARM_REG_R3)
            param4 = self.ql.register(UC_ARM_REG_R4)
            param5 = self.ql.register(UC_ARM_REG_R5)
        elif self.ql.archtype== QL_ARCH.MIPS32:
            param0 = self.ql.register(UC_MIPS_REG_A0)
            param1 = self.ql.register(UC_MIPS_REG_A1)
            param2 = self.ql.register(UC_MIPS_REG_A2)
            param3 = self.ql.register(UC_MIPS_REG_A3)
            param4 = self.ql.register(UC_MIPS_REG_SP)
            param4 = param4 + 0x10
            param5 = self.ql.register(UC_MIPS_REG_SP)
            param5 = param5 + 0x14
        elif self.ql.archtype== QL_ARCH.X86:
            param0 = self.ql.register(UC_X86_REG_EBX)
            param1 = self.ql.register(UC_X86_REG_ECX)
            param2 = self.ql.register(UC_X86_REG_EDX)
            param3 = self.ql.register(UC_X86_REG_ESI)
            param4 = self.ql.register(UC_X86_REG_EDI)
            param5 = self.ql.register(UC_X86_REG_EBP)
        elif self.ql.archtype== QL_ARCH.X8664:
            param0 = self.ql.register(UC_X86_REG_RDI)
            param1 = self.ql.register(UC_X86_REG_RSI)
            param2 = self.ql.register(UC_X86_REG_RDX)
            param3 = self.ql.register(UC_X86_REG_R10)
            param4 = self.ql.register(UC_X86_REG_R8)
            param5 = self.ql.register(UC_X86_REG_R9)                    
        
        return param0, param1, param2, param3, param4, param5