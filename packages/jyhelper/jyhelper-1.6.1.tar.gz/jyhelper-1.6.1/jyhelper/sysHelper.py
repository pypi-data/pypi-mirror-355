#! /usr/bin/env python3
# -*- coding:utf-8 -*-
# @Time : 2025/01/13 18:35 
# @Author : JY
"""
系统相关的操作
"""

import subprocess
import sys
import json


class sysHelper:

    @staticmethod
    def run_command(command, printInfo=True, returnStr=False, returnJson=False):
        """执行系统命令，实时显示输出，返回状态和结果"""
        lines = []
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True,
                                   universal_newlines=True)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                outStr = output.strip()
                lines.append(outStr)
                if printInfo:
                    print(outStr)
                    sys.stdout.flush()
        if returnStr:
            lines = ''.join(lines)
        if returnJson:
            lines = ''.join(lines)
            lines = json.loads(lines)
        # exit_code, lines
        return process.poll(), lines

    @staticmethod
    def red(msg):
        """print以后会显示亮红色字体"""
        return f"\033[91m{msg}\033[0m"

    @staticmethod
    def green(msg):
        """print以后会显示亮绿色字体"""
        return f"\033[92m{msg}\033[0m"

    @staticmethod
    def display_all_colors():
        """
        显示全部可用的颜色
        :return:
        """
        j = 0
        for i in range(108):
            if i in [2, 3, 5, 6, 8, 38, 39, 48, 49, 50, 98] or 10 <= i <= 20 or 22 <= i <= 29 or 52 <= i <= 89:
                continue
            msg = f"\033[{i}m" + r"\033[%sm内容\033[0m" % i + "\033[0m"
            if i < 10:
                msg += " "
            if i < 100:
                msg += " "
            print(msg, '', '', end='')
            j += 1
            if j % 8 == 0:
                print()

    @staticmethod
    def logError(msg1='', msg2='', msg3=''):
        """1个参数默认就是红色，2个或者3个参数msg2是红色"""
        if msg2 == '' and msg3 == '':
            print(sysHelper.red(msg1))
        elif msg2 != '' and msg3 == '':
            print(msg1, sysHelper.red(msg2))
        elif msg2 != '' and msg3 != '':
            print(msg1, sysHelper.red(msg2), msg3)

    @staticmethod
    def logInfo(msg1='', msg2='', msg3=''):
        if msg2 == '' and msg3 == '':
            print(sysHelper.green(msg1))
        elif msg2 != '' and msg3 == '':
            print(msg1, sysHelper.green(msg2))
        elif msg2 != '' and msg3 != '':
            print(msg1, sysHelper.green(msg2), msg3)


if __name__ == '__main__':
    sysHelper.display_all_colors()
