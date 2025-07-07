import os
import subprocess
import json
from pathlib import Path

def get_video_info(video_path):
    """获取视频文件的详细信息"""
    if not os.path.exists(video_path):
        return {"error": f"文件不存在: {video_path}"}
    
    # 获取文件基本信息
    file_stat = os.stat(video_path)
    file_info = {
        "文件名": os.path.basename(video_path),
        "文件大小": f"{file_stat.st_size / (1024*1024):.2f} MB",
        "创建时间": file_stat.st_ctime,
        "修改时间": file_stat.st_mtime,
        "访问权限": oct(file_stat.st_mode)[-3:]
    }
    
    try:
        # 使用 ffprobe 获取视频详细信息
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            video_data = json.loads(result.stdout)
            
            # 提取关键信息
            video_info = {
                "文件信息": file_info,
                "格式信息": {
                    "格式名称": video_data.get('format', {}).get('format_name', '未知'),
                    "时长": f"{float(video_data.get('format', {}).get('duration', 0)):.2f} 秒",
                    "比特率": f"{int(video_data.get('format', {}).get('bit_rate', 0))/1000:.2f} kbps"
                },
                "视频流": [],
                "音频流": []
            }
            
            # 处理视频和音频流
            for stream in video_data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_info["视频流"].append({
                        "编码格式": stream.get('codec_name', '未知'),
                        "分辨率": f"{stream.get('width', 0)}x{stream.get('height', 0)}",
                        "帧率": eval(stream.get('r_frame_rate', '0/1')),
                        "像素格式": stream.get('pix_fmt', '未知')
                    })
                elif stream.get('codec_type') == 'audio':
                    video_info["音频流"].append({
                        "编码格式": stream.get('codec_name', '未知'),
                        "采样率": f"{stream.get('sample_rate', 0)} Hz",
                        "声道数": stream.get('channels', 0),
                        "声道布局": stream.get('channel_layout', '未知')
                    })
            
            return video_info
        else:
            return {
                "文件信息": file_info,
                "error": f"ffprobe 执行失败: {result.stderr}"
            }
            
    except Exception as e:
        return {
            "文件信息": file_info,
            "error": f"处理视频时出错: {str(e)}"
        }

def main():
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    video_path = project_root / 'static' / 'source' / 'video' / 'gc2048.com-圣杯.mp4'
    
    # 获取视频信息
    info = get_video_info(str(video_path))
    
    # 打印信息
    print("\n=== 视频文件信息 ===")
    print(json.dumps(info, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main() 