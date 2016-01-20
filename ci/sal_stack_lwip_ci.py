#!/usr/bin/env python

"""
##############################################################################
# sa_stack_lwip_ci.py
#  CI (noclone) automation script to invoke sal-test module testing.
#
# This script overcomes the following problems:
# - sal-test is dependent on changes in the sal-stack-lwip module that 
#   havent been published in the yotta registry. Thus when sal-test
#   builds with the yotta published version the build would break. This
#   is overcome by git cloning sal-stack-lwip (to get HEAD with changes)
#   and using yt link in sal-test to use that version of sal-stack-lwip.
#
# In summary, this is what the script is doing
#   $ git clone git@github.com:/ARMmbed/sal-test.git sal-test
#   $ git clone git@github.com:/ARMmbed/sal-stack-lwip.git sal-stack-lwip_fixup
#   $ pushd sal-stack-lwip_fixup
#   $ yt link
#   $ popd
#   $ pushd sal-test
#   $ yt link sal-stack-lwip_fixup
#   $ yt target frdm-k64f-gcc
#   $ yt build
#
# Example usage: 
#     $ sal_test_ci.py 
#
# Author: simon.hughes@arm.com
###############################################################################
"""

import subprocess
import argparse
import sys
import os      
import time
import datetime

# error codes are positive numbers because sys.exit() returns a +ve number to the env
MBED_SUCCESS = 0
MBED_FAILURE = 1
MBED_ERROR_MAX = 2

g_debug = True
#g_debug = False

# a debug trace function
def dbg(str):
    if g_debug:
        print str
    return


##############################################################################
# sal_test
##############################################################################
class sal_test:
    """A class to manage the test"""

    def __init__(self):
        ts = time.time()
        self.datestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d_%H%M%S')

    # function to execute a bash command
    def doBashCmd(self, strBashCommand):
        ret = subprocess.call(strBashCommand.split(), shell=True)
        return ret

    def sal_stack_lwip_symlink(self):
        ret = MBED_FAILURE

        dbg(sys._getframe().f_code.co_name + ":entered")
        dbg(sys._getframe().f_code.co_name + ":ret=" + str(ret))
        
        # note the use of backslash as the file separator
        bashCommand = "pushd sal-stack-lwip\yotta_modules && mv sal sal_" + self.datestamp + " && junction.exe sal ../../sal && popd"
        ret = self.doBashCmd(bashCommand)
        if ret != MBED_SUCCESS:
            dbg(sys._getframe().f_code.co_name + ": failed to yotta link sal.") 
            return ret;
    
        return ret

    def sal_stack_lwip_unsymlink(self):
        ret = MBED_FAILURE

        dbg(sys._getframe().f_code.co_name + ":entered")
        dbg(sys._getframe().f_code.co_name + ":ret=" + str(ret))
        
        bashCommand = "pushd sal-stack-lwip/yotta_modules && junction.exe -d sal" 
        ret = self.doBashCmd(bashCommand)
        if ret != MBED_SUCCESS:
            dbg(sys._getframe().f_code.co_name + ": failed to yotta link sal-stack-lwip.") 
            return ret;
 
        return ret


    ##############################################################################
    # FUNCTION: run()
    #  this is the main function that implements the functionality
    ##############################################################################
		     
    def run(self, args):
        ret = MBED_FAILURE

        dbg(sys._getframe().f_code.co_name + ":entered")
        dbg(sys._getframe().f_code.co_name + ":ret=" + str(ret))
        
        
        # CI (i.e. jenkins) is setup to clone the sal-test and sal-stack-lwip repos so
        # the cloning of the repos is not required. The noclone option allows the 
        # cloning of the repos to be skipped
        if args.noclone is False:
            # e.g. running outside of noclone so dont clone repositories
        
            bashCommand = "git clone git@github.com:/simonqhughes/sal.git sal" 
            ret = self.doBashCmd(bashCommand)
            if ret != MBED_SUCCESS:
                dbg(sys._getframe().f_code.co_name + ": failed to clone sal repo.") 
                return ret;
                
            bashCommand = "git clone git@github.com:/simonqhughes/sal-stack-lwip.git sal-stack-lwip" 
            ret = self.doBashCmd(bashCommand)
            if ret != MBED_SUCCESS:
                dbg(sys._getframe().f_code.co_name + ": failed to clone sal-stack-lwip repo.") 
                return ret

        # set the target first as this is required by other commands.
        bashCommand = "pushd sal-stack-lwip && yotta target frdm-k64f-gcc && popd" 
        ret = self.doBashCmd(bashCommand)
        if ret != MBED_SUCCESS:
            dbg(sys._getframe().f_code.co_name + ": failed to set yotta target.") 
            return ret

        bashCommand = "pushd sal-stack-lwip && yotta -t frdm-k64f-gcc install && popd" 
        ret = self.doBashCmd(bashCommand)
        if ret != MBED_SUCCESS:
            dbg(sys._getframe().f_code.co_name + ": failed to yotta install in pushd sal-stack-lwip.") 
            return ret

        ret = self.sal_stack_lwip_symlink()
        if ret != MBED_SUCCESS:
            return ret
            
        bashCommand = "pushd sal-stack-lwip && yotta list && popd" 
        ret = self.doBashCmd(bashCommand)
        if ret != MBED_SUCCESS:
            dbg(sys._getframe().f_code.co_name + ": failed to yotta list in sal.")
            self.sal_stack_lwip_unsymlink()
            return ret

        bashCommand = "pushd sal-stack-lwip && yotta build && popd" 
        ret = self.doBashCmd(bashCommand)
        if ret != MBED_SUCCESS:
            dbg(sys._getframe().f_code.co_name + ": failed to yotta build.") 
            self.sal_stack_lwip_unsymlink()
            return ret

        bashCommand = "pushd sal-stack-lwip && yotta build && popd" 
        ret = self.doBashCmd(bashCommand)
        if ret != MBED_SUCCESS:
            dbg(sys._getframe().f_code.co_name + ": failed to yotta build.") 
            self.sal_stack_lwip_unsymlink()
            return ret

        bashCommand = "pushd sal-stack-lwip && mbedgt -V && popd" 
        ret = self.doBashCmd(bashCommand)
        if ret != MBED_SUCCESS:
            dbg(sys._getframe().f_code.co_name + ": failed to yotta build.") 
            self.sal_stack_lwip_unsymlink()
            return ret

        ret = self.sal_stack_lwip_unsymlink()
        if ret != MBED_SUCCESS:
            return ret

if __name__ == "__main__":

    ret = MBED_FAILURE
    test = sal_test()

    # command line argment setup and parsing
    parser = argparse.ArgumentParser()
    # noclone options. todo: will be used when develop
    parser.add_argument('--noclone', action='store_true', help='using this option => no clones of sal and sal-stack-lwip dirs')
    args = parser.parse_args()
    ret = test.run(args)
    sys.exit(ret)


    




