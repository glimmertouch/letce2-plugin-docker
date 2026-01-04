#!/usr/bin/env python3

"""
Docker Container Plugin for letce2

"""

import argparse
import sys
import os
import subprocess
import time
from pathlib import Path
from typing import List

from letce2.interface.plugin import Plugin as PluginBase
from letce2.engine.build import *



class Plugin(PluginBase):
    """Docker container plugin for letce2 experiments"""
    
    def __init__(self, name, argument_parser: argparse._SubParsersAction):
        """
        Initialize the Docker plugin
        
        Args:
            name: Plugin name
            argument_parser: ArgumentParser subparsers object
        """
        docker_subparser = argument_parser.add_parser(
            name,
            help='Execute experiments using Docker containers'
        )
        
        subparsers = docker_subparser.add_subparsers(
            help=f'{name} sub-command help'
        )
        
        # Build command - 生成配置文件
        subparser_build = subparsers.add_parser(
            'build',
            help='Generate all experiment configuration files'
        )
        subparser_build.add_argument(
            'experiment-config',
            nargs='*',
            type=str,
            default=["experiment.cfg"],
            help='configuration file.')
        subparser_build.add_argument(
            '--lock-file',
            type=str,
            metavar='FILE',
            default='/var/run/lock/letce.lock',
            help='Lock file location'
        )
        subparser_build.add_argument(
            '--force',
            action='store_true',
            help='Ignore existing lock file'
        )
        subparser_build.set_defaults(plugin_subcommand='build')
        
        # Start command - 启动容器
        subparser_start = subparsers.add_parser(
            'start',
            help='Start the Docker experiment'
        )
        subparser_start.add_argument(
            '-e', '--environment',
            type=str,
            metavar='FILE',
            default='',
            help='Environment file to source'
        )
        subparser_start.add_argument(
            '--compose-file',
            type=str,
            default='docker-compose.yml',
            help='Docker Compose file [default: %(default)s]'
        )
        subparser_start.add_argument(
            '--lock-file',
            type=str,
            metavar='FILE',
            default='/var/run/lock/letce.lock',
            help='Lock file location'
        )
        subparser_start.add_argument(
            '--force',
            action='store_true',
            help='Ignore existing lock file'
        )
        
        subparser_start.add_argument(
            '--scenario-delay',
            type=int,
            metavar='SECONDS',
            default=40,
            help='delay scenario for specified seconds [default: %(default)s].')

        subparser_start.set_defaults(plugin_subcommand='start')
        
        # Stop command - 停止容器
        subparser_stop = subparsers.add_parser(
            'stop',
            help='Stop the Docker experiment'
        )
        subparser_stop.add_argument(
            '-e', '--environment',
            type=str,
            metavar='FILE',
            default='',
            help='Environment file to source'
        )
        subparser_stop.add_argument(
            '--compose-file',
            type=str,
            default='docker-compose.yml',
            help='Docker Compose file'
        )
        subparser_stop.add_argument(
            '--lock-file',
            type=str,
            metavar='FILE',
            default='/var/run/lock/letce.lock',
            help='Lock file location'
        )
        subparser_stop.add_argument(
            '--force',
            action='store_true',
            help='Ignore missing lock file'
        )
        subparser_stop.set_defaults(plugin_subcommand='stop')
        
        # Clean command - 清理配置
        subparser_clean = subparsers.add_parser(
            'clean',
            help='Delete all generated configuration and output files'
        )
        subparser_clean.add_argument(
            '--lock-file',
            type=str,
            metavar='FILE',
            default='/var/run/lock/letce.lock',
            help='Lock file location'
        )
        subparser_clean.add_argument(
            '--force',
            action='store_true',
            help='Ignore missing lock file'
        )
        subparser_clean.set_defaults(plugin_subcommand='clean')
        
        docker_subparser.set_defaults(subcommand=name)
    
    def process(self, nodes_include, nodes_exclude, args):
        """
        Process plugin commands
        
        Args:
            nodes_include: List of nodes to include
            nodes_exclude: List of nodes to exclude
            args: Command arguments dict
        """
        print("hello")

        match args['plugin_subcommand']:
            case 'build':
                self._do_build(args)
            case 'start':
                self._do_start(nodes_include,args)
            case 'stop':
                self._do_stop(nodes_include,args)
            case 'clean':
                self._do_clean(nodes_include,nodes_exclude,args)
            case _:
                print(f"❌ Unknown subcommand: {args['plugin_subcommand']}", file=sys.stderr)
                sys.exit(1)
    
    def _do_build(self, args):
        """Generate experiment configuration files"""
        print("🔨 Building Docker experiment configuration...")
        
        # 检查锁文件
        if os.path.exists(args['lock_file']) and not args['force']:
            print(f"❌ Lock file found: {args['lock_file']}", file=sys.stderr)
            print("   Run `letce2 docker stop` first or use '--force'", file=sys.stderr)
            sys.exit(1)
        
        
        nodes = build_configuration(
            args['experiment-config'],
            args['include_filter'],
            args['exclude_filter'],
            args['include_file'],
            args['exclude_file'],
            args['manifest'],
            'letce2.plugins.docker'  # 用于模板查找
        )
        print(f"✅ Built configuration for {len(nodes)} nodes")

    
    def _do_start(self, nodes, args):
        """Start Docker containers"""
        print("Starting Docker experiment...")
        
        # check lock file
        if Path(args['lock_file']).exists() and not args['force']:
            print(f"❌ Lock file found: {args['lock_file']}", file=sys.stderr)
            print("   Run `letce2 docker stop` first or use '--force'", file=sys.stderr)
            sys.exit(1)
        
        for node in nodes:  
            Path(f'persist/{node}/var/run').mkdir(parents=True, exist_ok=True)
            Path(f'persist/{node}/var/log').mkdir(parents=True, exist_ok=True)
            Path(f'persist/{node}/var/tmp').mkdir(parents=True, exist_ok=True)
        
        
        
        
        compose_file = Path("host/docker-compose.yml")
        if compose_file.exists() is False:
            print(f"⚠️  Docker Compose file not found: {compose_file}", file=sys.stderr)
            sys.exit(1)

        try:
            print(f"📦 Starting containers from {compose_file}...")
            subprocess.run(
                ['docker', 'compose', '-f', str(compose_file), 'up', '-d'],
                check=True,
                capture_output=True,
                text=True
            )
            
            print("✅ Docker experiment started successfully")
            print(f"   Use `docker compose -f {compose_file} ps` to check status")
            
            Path(args['lock_file']).parent.mkdir(parents=True, exist_ok=True)
            Path(args['lock_file']).touch()
            
            
                        
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start containers: {e}", file=sys.stderr)
            if e.stderr:
                print(e.stderr, file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
            
        # RFC 2822
        start_utc = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
                                  time.gmtime(time.time() + args['scenario_delay']))

        # host: build veth links, generate eel and start broker
        try:
            subprocess.run(['sudo',
                             'host/control',
                             'prestart',
                             os.getcwd(),
                             args['environment'],
                             start_utc])

            subprocess.run(['sudo',
                             'host/bridge',
                             'start'])

            # disable realtime scheduling contraints
            subprocess.run(['sudo',
                             'sysctl',
                             'kernel.sched_rt_runtime_us=-1'])

            subprocess.run(['sudo',
                             'host/control',
                             'start',
                             os.getcwd(),
                             args['environment'],
                             start_utc])
        except Exception as e:
            print(f"❌ Error during experiment start: {e}", file=sys.stderr)
            sys.exit(1)
            
        print("🚀 Initializing nodes...")
        for node in nodes:
            if node == 'host':
                continue
            
            emane_node = f"letce2-{node}-emane"
            top_dir = "/experiment"
            env = "" # pre-built into container
            log_path = f"./persist/{node}/var/log/init.log"
            exec_cmd = [
                'docker', 'exec', emane_node,
                'bash', '-c',
                f"/experiment/{node}/init {top_dir} {node} '{env}' '{start_utc}'"
            ]
            with open(log_path, 'w') as log_file:
                subprocess.Popen(exec_cmd, stdout=log_file, stderr=subprocess.STDOUT)
            
            biz_node = f"letce2-{node}-biz"
            log_path = f"./persist/{node}/var/log/biz_init.log"
            exec_cmd = [
                'docker', 'exec', biz_node,
                'bash', '-c',
                f"/experiment/{node}/biz-init {top_dir} {node} '{env}' '{start_utc}'"
            ]
            with open(log_path, 'w') as log_file:
                subprocess.Popen(exec_cmd, stdout=log_file, stderr=subprocess.STDOUT)
        
    
    def _do_stop(self, nodes, args):
        """Stop Docker containers"""
        print("🛑 Stopping Docker experiment...")
        
        compose_file = Path("host/docker-compose.yml")
        
        if not compose_file.exists():
            print(f"⚠️  Docker Compose file not found: {compose_file}", file=sys.stderr)
            if not args['force']:
                sys.exit(1)
        
        try:
            print("📦 Stopping and removing containers...")
            subprocess.run(
                ['docker', 'compose', '-f', str(compose_file), 'down'],
                check=True,
                capture_output=True,
                text=True
            )
            
            
            print("✅ Docker experiment stopped successfully")
            
            # 删除锁文件
            if Path(args['lock_file']).exists():
                Path(args['lock_file']).unlink()
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to stop containers: {e}", file=sys.stderr)
            if e.stderr:
                print(e.stderr, file=sys.stderr)
            if not args['force']:
                sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
            
        try:
            # not necessary because docker compose down already stop containers
            # subprocess.run(['sudo',
            #                  'host/bridge',
            #                  'stop'])
            
            subprocess.run(['sudo',
                             'host/control',
                             'stop',
                             os.getcwd(),
                             args['environment']])
        except Exception as e:
            print(f"❌ Error during experiment stop: {e}", file=sys.stderr)
            sys.exit(1)
        
        subprocess.run(['sudo',
                         'sysctl',
                         'kernel.sched_rt_runtime_us=950000'])
    
    def _do_clean(self, nodes_include, nodes_exclude, args):
        """Clean up generated files"""
        print("🧹 Cleaning experiment files...")
        
        # 检查锁文件
        if Path(args['lock_file']).exists() and not args['force']:
            print(f"❌ Lock file found: {args['lock_file']}", file=sys.stderr)
            print("   Run `letce2 docker stop` first or use '--force'", file=sys.stderr)
            sys.exit(1)
        
        if not nodes_exclude:
            if Path('persist').exists() and Path('persist').is_dir():
                subprocess.call(['sudo',
                                 'rm',
                                 '-rf',
                                 'persist'])
        else:
            for node in nodes_include:
                if Path(f'persist/{node}').exists() and Path(f'persist/{node}').is_dir():
                    subprocess.call(['sudo',
                                     'rm',
                                     '-rf',
                                     f'persist/{node}'])
            nodes_to_manifest(nodes_exclude,
                              args['manifest'])

        
        try:
            clean_configuration(nodes_include, args['manifest'])
            print("✅ Cleaned up experiment files")
        except Exception as e:
            print(f"❌ Clean failed: {e}", file=sys.stderr)
            sys.exit(1)
    
