#!/usr/bin/env python
import subprocess
import glob
import os
import re
import time
import graph

import hash_lib

# subprocess内でルートを指定したいときの書き方
# os.path.expanduser('~/')
pkgName = ''
buildCmd = ''

# call graph singleton instance
graph = graph.Graph.getInstance()

# 最初の処理で/buildTrace/pkgName内を全削除するため確認を取るための関数
def yes_no_input():
    while True:
        choice = input("/buildTrace/" + pkgName + "/内部のデータが全て消えますがよろしいですか？ [y/N]: ").lower()
        if choice in ['y', 'ye', 'yes']:
            return True
        elif choice in ['n', 'no']:
            return False

# main関数
def straceExe(buildCmd_, pkgName_):
    global pkgName, buildCmd
    pkgName = pkgName_
    buildCmd = buildCmd_
    removeDir()
    makeDir()
    strace()
    log_edit()
    file_exist()
    backup()
    except_change_file()
    hash_output()

    countTimeList = ['build and strace','edit log', 'file exist check', 'files backup', 'calc hash']
    exeTime_edit(countTimeList)

# def timeCount(func, funcName: str):
#     start = time.perf_counter()
#     func
#     end = time.perf_counter()
#     time_elapsed = end - start
#     with open('./buildTrace/logs/times/exeTimes.txt', 'a') as f:
#         f.write(funcName + ' execution time : ' + '{:.20f}'.format(time_elapsed) + '\n')

def countTime(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        func(*args, **kwargs)
        end = time.perf_counter()
        time_elapsed = end - start
        with open('/buildTrace/' + pkgName + '/logs/times/exeTimes.txt', 'a') as f:
            f.write('{:.20f}'.format(time_elapsed) + '\n')
    return wrapper

def removeDir():
    # /buildTrace/pkgName/ディレクトリ内を削除
    cmd = 'rm -rf /buildTrace/' + pkgName + '/*'
    logs = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
    # print(logs.stdout.decode())

def makeDir():
    # 必要なディレクトリを作成
    cmd = ['mkdir', '-p', '/buildTrace/' + pkgName + '/backup']
    logs = subprocess.run(cmd, stdout=subprocess.PIPE)
    cmd = ['mkdir', '/buildTrace/' + pkgName + '/backup/input']
    logs = subprocess.run(cmd, stdout=subprocess.PIPE)
    cmd = ['mkdir', '/buildTrace/' + pkgName + '/backup/output']
    logs = subprocess.run(cmd, stdout=subprocess.PIPE)
    cmd = ['mkdir', '/buildTrace/' + pkgName + '/backup/command']
    logs = subprocess.run(cmd, stdout=subprocess.PIPE)
    cmd = ['mkdir', '/buildTrace/' + pkgName + '/backup/hash']
    logs = subprocess.run(cmd, stdout=subprocess.PIPE)
    cmd = ['mkdir', '-p', '/buildTrace/' + pkgName + '/logs/times']
    logs = subprocess.run(cmd, stdout=subprocess.PIPE)
    # print(logs.stdout.decode())

@countTime
def strace():
    # ビルドコマンド入力，加工
    buildcmd = buildCmd
    if buildcmd == '':
        buildcmd = input("Please Enter build command : ")
    cmd = 'strace -ff -e trace=openat,open -o /buildTrace/' + pkgName + '/logs/strace_out.txt ' + buildcmd

    hash_cmd = hash_lib.sha256string(buildcmd)     # encryte build command to hash
    graph.add_vertex(hash_cmd) # add hash to graph

    # straceコマンドを使用 /buildTrace/にout.txt.????として出力(????はPID)
    logs = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
    # print(logs.stdout.decode())

    # ビルドコマンドを/buildTrace/backup/commandにテキストとして保存
    file = open('/buildTrace/' + pkgName + '/backup/command/buildCommand.txt', 'wt')
    file.write(buildcmd)
    file.close()

@countTime
def log_edit():
    # /buildTrace/ディレクトリ内にリダイレクトされたファイル名のリストを取得
    file_list = glob.glob("/buildTrace/" + pkgName + "/logs/*.txt*")
    # print(file_list)

    # 取得したファイル一つ一つに処理を行う
    for i in file_list:
        file = open(i)
        lines = file.read().splitlines()
        file.close()
        fileOut = open('/buildTrace/' + pkgName + '/logs/output_all.txt', 'a')
        fileIn = open('/buildTrace/' + pkgName + '/logs/input_all.txt', 'a')
        for line in lines:
            match = re.search(r'= -1 ENOENT', line)
            if match is None:
                match = re.match(r'---(.+)---', line)
                if match is None:
                    match = re.search(r'"(.+)".+(O_CREAT)', line)
                    # print(match)
                    if match is not None:
                        # print(match)
                        fileOut.write(match.group(1) + '\n')
                    else:
                        match = re.search(r'"(.+)"', line)
                        if match is not None:
                            fileIn.write(match.group(1) + '\n')
        fileOut.close()
        fileIn.close()

    # 処理後のファイルを結合し，out_all.txtとして出力
    # file_list_input = glob.glob("./buildTrace/logs/*_input")
    # file = open('./buildTrace/logs/input_all.txt', 'a')
    # for i in file_list_input:
    #     file.write(open(i).read())
    # file.close()

    # file_list_output = glob.glob("./buildTrace/logs/*_output")
    # file = open('./buildTrace/logs/output_all.txt', 'a')
    # for i in file_list_output:
    #     file.write(open(i).read())
    # file.close()

@countTime
def file_exist():
    # input_all.txtを開き，一行づつファイルの存在確認を行う
    file = open('/buildTrace/' + pkgName + '/logs/input_all.txt')
    lines = file.read().splitlines()
    file.close()

    file = open('/buildTrace/' + pkgName + '/logs/input_file_exist.txt', 'wt')
    for line in lines:
        # 存在したファイルパスのみテキストに書き出す
        exist = os.path.isfile(line)
        # print(exists)
        if exist:
            file.write(line+'\n')
    file.close()

    # output_all.txtを開き，一行づつファイルの存在確認を行う
    file = open('/buildTrace/' + pkgName + '/logs/output_all.txt')
    lines = file.read().splitlines()
    file.close()

    file = open('/buildTrace/' + pkgName + '/logs/output_file_exist.txt', 'wt')
    for line in lines:
        # 存在したファイルパスのみテキストに書き出す
        exist = os.path.isfile(line)
        # print(exists)
        if exist:
            file.write(line+'\n')
    file.close()

@countTime
def backup():
    # 書き出されたファイルパステキストを元にバックアップを作成
    file = open('/buildTrace/' + pkgName + '/logs/input_file_exist.txt')
    lines = file.read().splitlines()
    file.close()
    for i in lines:
        cmd = 'cp --parents ' + i + ' /buildTrace/' + pkgName + '/backup/input/'
        logs = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)

    file = open('/buildTrace/' + pkgName + '/logs/output_file_exist.txt')
    lines = file.read().splitlines()
    file.close()
    for i in lines:
        cmd = 'cp --parents ' + i + ' /buildTrace/' + pkgName + '/backup/output/'
        logs = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)

# 日にち情報が含まれているファイルをリストから除外する
def except_change_file():
    with open('/buildTrace/' + pkgName + '/logs/input_file_exist.txt') as f:
        lines = f.readlines()
        new_lines = []
        for i in lines:
            if re.search('.buildinfo', i) is None:
                new_lines.append(i)

        f = open('/buildTrace/' + pkgName + '/logs/input_file_exist.txt', 'wt')
        f.close()
        with open('/buildTrace/' + pkgName + '/logs/input_file_exist.txt', 'a') as new_f:
            for i in new_lines:
                new_f.write(i)

    with open('/buildTrace/' + pkgName + '/logs/output_file_exist.txt') as f:
        lines = f.readlines()
        new_lines = []
        for i in lines:
            if re.search('.+.change', i) is None:
                new_lines.append(i)

        f = open('/buildTrace/' + pkgName + '/logs/output_file_exist.txt', 'wt')
        f.close()
        with open('/buildTrace/' + pkgName + '/logs/output_file_exist.txt', 'a') as new_f:
            for i in new_lines:
                new_f.write(i)


@countTime
def hash_output():
    # バックアップからハッシュ値を計算しテキストに出力
    file = open('/buildTrace/' + pkgName + '/logs/input_file_exist.txt')
    lines = file.read().splitlines()
    file.close()
    logfile = open('/buildTrace/' + pkgName + '/backup/hash/input_hash_list.txt', 'wt')
    file = open('/buildTrace/' + pkgName + '/backup/hash/input_hash_only.txt', 'wt')
    for i in lines:
        checksum = hash_lib.sha256sum(i)
        logfile.write(checksum + ' : ' + i + '\n')
        file.write(checksum + '\n')
        graph.add_edge(checksum, buildCmd, i) # add edge connecting input file to build command
    logfile.close()
    file.close()

    file = open('/buildTrace/' + pkgName + '/logs/output_file_exist.txt')
    lines = file.read().splitlines()
    file.close()
    logfile = open('/buildTrace/' + pkgName + '/backup/hash/output_hash_list.txt', 'wt')
    file = open('/buildTrace/' + pkgName + '/backup/hash/output_hash_only.txt', 'wt')
    for i in lines:
        checksum = hash_lib.sha256sum(i)
        logfile.write(checksum + ' : ' + i + '\n')
        file.write(checksum + '\n')
        graph.add_edge(buildCmd, checksum, i) # add edge connecting build command to output file
    logfile.close()
    file.close()

    # ハッシュ値のリストをソート，重複削除
    file = open('/buildTrace/' + pkgName + '/backup/hash/input_hash_only.txt')
    lines = file.readlines()
    file.close()
    file = open('/buildTrace/' + pkgName + '/backup/hash/input_hash_only.txt', 'w+')
    file.writelines(sorted(set(lines)))
    file.close()

    file = open('/buildTrace/' + pkgName + '/backup/hash/output_hash_only.txt')
    lines = file.readlines()
    file.close()
    file = open('/buildTrace/' + pkgName + '/backup/hash/output_hash_only.txt', 'w+')
    file.writelines(sorted(set(lines)))
    file.close()

    # ハッシュ値を記録したテキストファイルをハッシュ化
    # sha256 = hashlib.sha256()
    # with open('/buildTrace/' + pkgName + '/backup/hash/input_hash_only.txt', 'rb') as f:
        # inputHash = hashlib.sha256(f.read().encode()).hexdigest()
    inputHash = hash_lib.sha256sum('/buildTrace/' + pkgName + '/backup/hash/input_hash_only.txt')

    # sha256 = hashlib.sha256()
    # with open('/buildTrace/' + pkgName + '/backup/hash/output_hash_only.txt', 'rb') as f:
        # outputHash = hashlib.sha256(f.read().encode()).hexdigest()
    outputHash = hash_lib.sha256sum('/buildTrace/' + pkgName + '/backup/hash/output_hash_only.txt')

    # with open('/buildTrace/' + pkgName + '/backup/command/buildCommand.txt', 'rb') as f:
        # commandHash = hashlib.sha256(f.read().encode()).hexdigest()
    commandHash = hash_lib.sha256sum('/buildTrace/' + pkgName + '/backup/command/buildCommand.txt')

    with open('/buildTrace/' + pkgName + '/backup/hash/hash_all.txt', 'wt') as f:
        f.write('inputHash   : ' + inputHash + '\n')
        f.write('outputHash  : ' + outputHash + '\n')
        f.write('commandHash : ' + commandHash + '\n')

#ハッシュ計算
# def sha256sum(filename):
#     h = hashlib.sha256()
#     with open(filename, 'rb', buffering=0) as f:
#         for b in iter(lambda : f.read(128*1024), b''):
#             h.update(b)
#     return h.hexdigest()

def exeTime_edit(funclist):
    exeTime_edit_List = []
    with open('/buildTrace/' + pkgName + '/logs/times/exeTimes.txt', 'r') as f:
        for funcName, line in zip(funclist, f.readlines()):
            exeTime_edit_List.append(funcName + ' : ' + line)
    with open('/buildTrace/' + pkgName + '/logs/times/exeTimes.txt', 'w') as f:
        f.writelines(exeTime_edit_List)