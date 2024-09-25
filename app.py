# follow main.py to create a web-based demo
import sys, os, shutil
sys.path.append(os.path.dirname(__file__))
import gradio as gr
import tkinter as tk

TRANSLATOR_SUPPORTED = [
    "sakura-009",
    "sakura-010",
    "index",
    "Galtransl",
    "gpt35-0613",
    "gpt35-1106",
    "gpt4-turbo",
    "moonshot-v1-8k",
    "glm-4",
    "glm-4-flash",
    "qwen2-7b-instruct",
    "qwen2-57b-a14b-instruct",
    "qwen2-72b-instruct",
    "abab6.5-chat",
    "abab6.5s-chat",
    "none",
]

def worker(input_files, yt_url, remove_adjacent_duplicates ,remove_short, restore_symbol, save_path, model_size, translator, gpt_token, sakura_address, proxy_address, before_dict, gpt_dict, after_dict):
    if not input_files:
        input_files = []
    output_files = []
    print("正在初始化项目文件夹...")
    if before_dict:
        with open('sampleProject/项目字典_译前.txt', 'w', encoding='utf-8') as f:
            f.write(before_dict.replace(' ','\t'))
    else:
        import os
        if os.path.exists('sampleProject/项目字典_译前.txt'):
            os.remove('sampleProject/项目字典_译前.txt')
    if gpt_dict:
        with open('sampleProject/项目GPT字典.txt', 'w', encoding='utf-8') as f:
            f.write(gpt_dict.replace(' ','\t'))
    else:
        import os
        if os.path.exists('sampleProject/项目GPT字典.txt'):
            os.remove('sampleProject/项目GPT字典.txt')
    if after_dict:
        with open('sampleProject/项目字典_译后.txt', 'w', encoding='utf-8') as f:
            f.write(after_dict.replace(' ','\t'))
    else:
        import os
        if os.path.exists('sampleProject/项目字典_译后.txt'):
            os.remove('sampleProject/项目字典_译后.txt')

    if yt_url and ('youtu.be' in yt_url or 'youtube.com' in yt_url):
        from yt_dlp import YoutubeDL
        import os
        if os.path.exists('sampleProject/YoutubeDL.webm'):
            os.remove('sampleProject/YoutubeDL.webm')
        with YoutubeDL({'proxy': proxy_address,'outtmpl': 'sampleProject/YoutubeDL.webm'}) as ydl:
            print("正在下载视频...")
            results = ydl.download([yt_url])
            print("视频下载完成！")
        input_files += ['sampleProject/YoutubeDL.webm']

    elif yt_url and 'BV' in yt_url:
        from bilibili_dl.bilibili_dl.Video import Video
        from bilibili_dl.bilibili_dl.downloader import download
        from bilibili_dl.bilibili_dl.utils import send_request
        from bilibili_dl.bilibili_dl.constants import URL_VIDEO_INFO
        print("正在下载视频...")
        res = send_request(URL_VIDEO_INFO, params={'bvid': yt_url})
        download([Video(
            bvid=res['bvid'],
            cid=res['cid'] if res['videos'] == 1 else res['pages'][0]['cid'],
            title=res['title'] if res['videos'] == 1 else res['pages'][0]['part'],
            up_name=res['owner']['name'],
            cover_url=res['pic'] if res['videos'] == 1 else res['pages'][0]['pic'],
        )], False)
        print("视频下载完成！")
        import re
        title = res['title'] if res['videos'] == 1 else res['pages'][0]['part']
        title = re.sub(r'[.:?/\\]', ' ', title).strip()
        title = re.sub(r'\s+', ' ', title)
        os.makedirs('sampleProject/cache', exist_ok=True)
        shutil.move(f'{title}.mp4', f'sampleProject/cache/{title}.mp4')
        input_files += [f'sampleProject/cache/{title}.mp4']
    
    output_file_paths = []
    audio_files = []
    files_end = {}
    output_audio_paths = []
    if restore_symbol:
        if os.path.exists('sampleProject/gt_input'):
            for file_name in os.listdir('sampleProject/gt_input'):
                if file_name.endswith('.json'):
                    output_file_paths.append(os.path.join('sampleProject/gt_input', file_name))
            for file_name in input_files:
                    file_end = '.' + file_name.split('.')[-1]
                    files_end[file_name] = file_end
    else:
        for input_file in input_files:
            if input_file and input_file.endswith('.srt'):
                if input_file.endswith('.jp.srt'):
                    files_end[input_file] = '.jp.srt'
                else:
                    files_end[input_file] = '.srt'
                from srt2prompt import make_prompt
                print("正在进行字幕转换...")
                import os
                os.makedirs('sampleProject/gt_input', exist_ok=True)
                output_file_path = os.path.join('sampleProject/gt_input', os.path.basename(input_file).replace('.jp','').replace('.srt','.json'))
                output_file_paths.append(output_file_path)
                make_prompt(input_file, output_file_path)
                if remove_adjacent_duplicates:
                    from prompt2srt import remove_duplicates
                    remove_duplicates(output_file_paths[-1], output_file_paths[-1])
                if remove_short:
                    from prompt2srt import remove_short_message
                    remove_short_message(output_file_paths[-1], output_file_paths[-1], 5)
                print("字幕转换完成！")
            elif input_file:
                audio_files.append(input_file)
                file_end = '.' + input_file.split('.')[-1]
                files_end[input_file] = file_end

        if audio_files:
            print("正在进行语音识别...")
            from whisper2prompt import execute_asr
            output_audio_paths = execute_asr(
                input_files  = audio_files,
                output_folder = 'sampleProject/gt_input',   
                model_size    = model_size,
                language      = 'ja',
                precision     = 'float16',
            )
            output_file_paths += output_audio_paths
            print("语音识别完成！")

    for output_file_path in output_file_paths:
        if remove_adjacent_duplicates:
            from prompt2srt import remove_duplicates
            remove_duplicates(output_file_path, output_file_path)
        if remove_short:
            from prompt2srt import remove_short_message
            remove_short_message(output_file_path, output_file_path, 5)

    if translator == 'none':
        print("无需进行翻译！")
        
        print("正在生成字幕文件...")
        from prompt2srt import make_srt, make_lrc
        for input_file, output_file_path in zip(input_files, output_file_paths):
            temp_end = files_end[input_file]
            input_file = input_file.replace(files_end[input_file],'')
            make_srt(output_file_path, input_file+'.jp.srt')
            make_lrc(output_file_path, input_file+'.jp.lrc')
            output_files += [
                input_file+'.jp.srt',
                input_file+'.jp.lrc',
            ]
        input_file = input_file + temp_end
        print("字幕文件生成完成！")
        print("输入输出缓存地址为：", os.path.dirname(input_file))
        
        if files_end[input_file] == '.mp3' or files_end[input_file] == '.wav':
            print("")
        else:
            output_files.append(input_file)
        if save_path:
            save_file(output_files, save_path)
        return output_files

    print("正在进行翻译配置...")
    with open('sampleProject/config.yaml', 'r', encoding='utf-8') as f:
        lines = f.readlines()

        for idx, line in enumerate(lines):
            if 'gpt' in translator and gpt_token:
                if 'GPT35' in line:
                    lines[idx+2] = f"      - token: {gpt_token}\n"
                    lines[idx+6] = f"    defaultEndpoint: https://api.openai.com\n"
                    lines[idx+7] = f'    rewriteModelName: ""\n'
                if 'GPT4' in line:
                    lines[idx+2] = f"      - token: {gpt_token}\n"
            if 'moonshot' in translator and gpt_token:
                if 'GPT35' in line:
                    lines[idx+4] = f"      - token: {gpt_token}\n"
                    lines[idx+6] = f"    defaultEndpoint: https://api.moonshot.cn\n"
                    lines[idx+7] = f'    rewriteModelName: "moonshot-v1-8k"\n'
            if 'qwen' in translator and gpt_token:
                if 'GPT35' in line:
                    lines[idx+4] = f"      - token: {gpt_token}\n"
                    lines[idx+6] = f"    defaultEndpoint: https://dashscope.aliyuncs.com/compatible-mode\n"
                    lines[idx+7] = f'    rewriteModelName: "{translator}"\n'
            if 'glm' in translator and gpt_token:
                if 'GPT35' in line:
                    lines[idx+4] = f"      - token: {gpt_token}\n"
                    lines[idx+6] = f"    defaultEndpoint: https://open.bigmodel.cn/api/paas\n"
                    lines[idx+7] = f'    rewriteModelName: "{translator}"\n'
            if 'abab' in translator and gpt_token:
                if 'GPT35' in line:
                    lines[idx+4] = f"      - token: {gpt_token}\n"
                    lines[idx+6] = f"    defaultEndpoint: https://api.minimax.chat\n"
                    lines[idx+7] = f'    rewriteModelName: "{translator}"\n'
            if ('sakura' in translator or 'index' in translator or 'Galtransl' in translator) and sakura_address:
                if 'Sakura' in line:
                    lines[idx+1] = f"    endpoint: {sakura_address}\n"
            if proxy_address:
                if 'proxy' in line:
                    lines[idx+1] = f"  enableProxy: true\n"
                    lines[idx+3] = f"    - address: {proxy_address}\n"
            else:
                if 'proxy' in line:
                    lines[idx+1] = f"  enableProxy: false\n"

        if 'moonshot' in translator or 'qwen' in translator or 'glm' in translator or 'abab' in translator:
            translator = 'gpt35-0613'
        
        if 'index' in translator:
            translator = 'sakura-009'

        if 'Galtransl' in translator:
            translator = 'sakura-010'

        with open('sampleProject/config.yaml', 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print("正在进行翻译...")
        from GalTransl.__main__ import worker
        worker('sampleProject', 'config.yaml', translator, show_banner=False)

    print("正在生成字幕文件...")
    from prompt2srt import make_srt, make_lrc
    for input_file,output_file_path in zip(input_files, output_file_paths):
        temp_end = files_end[input_file]
        input_file = input_file.replace(files_end[input_file],'').replace('.jp','')
        make_srt(output_file_path.replace('gt_input','gt_output'), input_file+'.srt')
        make_lrc(output_file_path.replace('gt_input','gt_output'), input_file+'.lrc')
        make_srt(output_file_path, input_file+'.jp.srt')
        make_lrc(output_file_path, input_file+'.jp.lrc')
        output_files += [
            input_file+'.lrc', 
            input_file+'.srt', 
            input_file+'.jp.srt', 
            input_file+'.jp.lrc', 
        ]
    # input_file = input_file + temp_end
    print("字幕文件生成完成！")
    # print("缓存地址为：", input_file)
    try:
        if files_end[input_file] != '.mp3' or files_end[input_file] != '.wav' or files_end[input_file] != '.srt':
            output_files.append(input_file+files_end[input_file])
    finally:
        if save_path:
            save_file(output_files, save_path)
        return output_files

def cleaner():
    print("正在清理中间文件...")
    if os.path.exists('sampleProject/gt_input'):
        shutil.rmtree('sampleProject/gt_input')
    if os.path.exists('sampleProject/gt_output'):
        shutil.rmtree('sampleProject/gt_output')
    if os.path.exists('sampleProject/transl_cache'):
        shutil.rmtree('sampleProject/transl_cache')
    print("正在清理输出...")
    if os.path.exists('sampleProject/cache'):
        shutil.rmtree('sampleProject/cache')
    return []

def select_path():
    from tkinter import filedialog
    root = tk.Tk()
    root.wm_attributes('-topmost',1)
    root.withdraw()
    return filedialog.askdirectory()

def save_file(files, save_path):
    try:
        for file in files:
            shutil.copy(file, save_path)
    except:
        print("保存文件失败！")

def zip_files(output_files, endwith):
    import zipfile
    os.makedirs('sampleProject/cache', exist_ok=True)
    with zipfile.ZipFile(f'sampleProject/cache/output_{endwith}.zip', 'w') as zipf:
        for output_file in output_files:
            if output_file.endswith(endwith):
                if '.jp' in endwith and '.jp' in output_file:
                    zipf.write(output_file, os.path.basename(output_file))
                elif '.jp' not in endwith and '.jp' not in output_file:
                    zipf.write(output_file, os.path.basename(output_file))
    return f'sampleProject/cache/output_{endwith}.zip'

with gr.Blocks() as demo:
    gr.Markdown("# 欢迎使用GalTransl for ASMR！")
    gr.Markdown("您可以使用本程序将日语音视频文件/字幕文件转换为中文字幕文件。")
    input_files = gr.Files(label="1. 请选择音视频文件/SRT文件（或拖拽文件到窗口）")
    yt_url = gr.Textbox(label="输入YouTube视频链接（包含youtu.be或者youtube.com）或者Bilibili的BV号进行下载。", placeholder="https://www.youtube.com/watch?v=...")
    model_size = gr.Radio(
        label="2. 请选择语音识别模型大小:",
        choices=['small', 'medium', 'large-v3',],
        value='small'
    )
    translator = gr.Radio(
        label="3. 请选择翻译器：",
        choices=TRANSLATOR_SUPPORTED,
        value='none'
    )
    gpt_token = gr.Textbox(label="4. 请输入 API Token (GPT, Moonshot, Qwen, GLM, MiniMax/abab)", placeholder="留空为使用上次配置的Token")
    sakura_address = gr.Textbox(label="6. 请输入 API 地址 (Sakura, Index, Galtransl)", placeholder="例如：http://127.0.0.1:8080，留空为使用上次配置的地址")
    proxy_address = gr.Textbox(label="7. 请输入翻译引擎和视频下载代理地址", placeholder="例如：http://127.0.0.1:7890，留空为不使用代理")
    with gr.Accordion("8. 使用翻译字典（可选）", open=False):
        with gr.Row():
            before_dict = gr.Textbox(label="输入替换字典（日文到日文）", placeholder="日文\t日文\n日文\t日文")
            gpt_dict = gr.Textbox(label="翻译替换字典（日文到中文，不支持sakura-009，Index）", placeholder="日文\t中文\n日文\t中文")
            after_dict = gr.Textbox(label="输出替换字典（中文到中文）", placeholder="中文\t中文\n中文\t中文")

    with gr.Row():
        with gr.Column(scale=15):
            save_path = gr.Textbox(label="保存文件路径(可选)",scale=4)
        with gr.Column(scale=1,min_width=20):
            gr.Button("选择路径").click(select_path, inputs=[], outputs=save_path)

    remove_adjacent_duplicates = gr.Checkbox(label="去除相邻重复")
    remove_short = gr.Checkbox(label="去除短句（建议下载.jp.srt手动去除）")
    restore_symbol = gr.Checkbox(label="恢复进度（在已经进行语音识别的情况下使用）")
    run = gr.Button("9. 运行（状态详情请见命令行）")
    outputs = gr.Files(label="输出文件")

    output_zip_file = gr.File(label="打包输出文件")

    with gr.Row():
        gr.Button("打包下载srt").click(zip_files, inputs=[outputs, gr.Textbox(value='.srt', visible=False)],outputs=output_zip_file)
        gr.Button("打包下载lrc").click(zip_files, inputs=[outputs, gr.Textbox(value='.lrc', visible=False)],outputs=output_zip_file)
        gr.Button("打包下载jp.srt").click(zip_files, inputs=[outputs, gr.Textbox(value='.jp.srt', visible=False)],outputs=output_zip_file)
        gr.Button("打包下载jp.lrc").click(zip_files, inputs=[outputs, gr.Textbox(value='.jp.lrc', visible=False)],outputs=output_zip_file)
    clean = gr.Button("10.清空输入输出缓存（请在使用完成后点击）")

    run.click(worker, inputs=[input_files, yt_url, remove_adjacent_duplicates, remove_short, restore_symbol, save_path, model_size, translator, gpt_token, sakura_address, proxy_address, before_dict, gpt_dict, after_dict], outputs=outputs, queue=True)
    clean.click(cleaner, inputs=[],outputs=outputs)

demo.queue().launch(inbrowser=False, server_name='0.0.0.0')
