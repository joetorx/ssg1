#!/usr/bin/env python3

# Copyright (c) 2026 Joel Torres
# Licensed under the MIT License. See the file LICENSE for details.

import os
import sys
import argparse
import markdown
import json
import shutil
import datetime
import site
import socketserver
from pathlib import Path
from dataclasses import dataclass
from collections import OrderedDict
from http.server import SimpleHTTPRequestHandler
from jinja2 import Environment, FileSystemLoader
from markupsafe import escape

__version__ = '2026.5.10'

@dataclass
class Config:
    env = Environment(
        loader=FileSystemLoader('_templates')
    )

    local_assets = Path('ssg1/assets') # for test only
    site_assets = Path(site.getsitepackages()[0], 'ssg1/assets')
    home_assets = Path(os.getenv('HOME'), '.ssg1/assets')
    output_dir = Path('www')
    templates_dir = Path('_templates')
    styles_dir = Path('styles')
    scripts_dir = Path('scripts')
    images_dir = Path('images')
    blog_dir = Path('blog')

    styles_output_dir = output_dir / styles_dir
    scripts_output_dir = output_dir / scripts_dir
    images_output_dir = output_dir / images_dir
    blog_output_dir = output_dir / blog_dir

    input_dirs = [templates_dir, styles_dir, 
                    scripts_dir, images_dir, blog_dir]

    output_dirs = [styles_output_dir, scripts_output_dir, 
                     images_output_dir, blog_output_dir]

    in_out_dir_map = [ (in_dir, out_dir) 
                       for in_dir, out_dir in zip(input_dirs[1:], output_dirs) ]

    config_file = Path('_config.json')
    lang = 'en-US'
    max_posts = 10
    excluded_files = ['README.md']

    base_nav = [('Home', '/'), ('Blog', '/blog/'), ('Tags', '/tags/')]
    nav_file = Path('_nav.json')

    slug_replace_map = str.maketrans({
        ' ' : '-',
        '/' : '-',
        '.' : '',
        '"' : '',
        "'" : '',
        '`' : '',
        '~' : '',
        '!' : '',
        '@' : '',
        '#' : '',
        '%' : '',
        '^' : '',
        '&' : '',
        '*' : '',
        '(' : '',
        ')' : '',
        '_' : '-',
        '=' : '',
        '+' : '',
        '[' : '',
        '{' : '',
        ']' : '',
        '}' : '',
        '|' : '',
        ';' : '',
        ',' : '',
        ':' : '',
        '<' : '',
        '>' : '',
        '?' : '',
        '\\' : '',
    })


conf = Config()

def init(args: argparse.Namespace) -> None:

    if conf.local_assets.exists():
        assets_home = conf.local_assets
    elif conf.home_assets.exists():
        assets_home = conf.home_assets
    elif conf.site_assets.exists():
        assets_home = conf.site_assets
    else:
        print('error: unable to locate assets')
        sys.exit(1)

    templates = assets_home / conf.templates_dir
    styles = assets_home / conf.styles_dir
    scripts = assets_home / conf.scripts_dir
    base_nav = OrderedDict(conf.base_nav) 

    save_config({})
    save_nav(base_nav)

    print(f'=> {conf.config_file}')
    print(f'=> {conf.nav_file}')
    for dirname in conf.input_dirs:
        print(f'=> {dirname}')
        dirname.mkdir(exist_ok=True)

    shutil.copytree(templates, conf.templates_dir, dirs_exist_ok=True)
    shutil.copytree(styles, conf.styles_dir, dirs_exist_ok=True)
    shutil.copytree(scripts, conf.scripts_dir, dirs_exist_ok=True)

    config(args)

    print('\nSite init finished.')
    print('Ensure the following configs are made before building the site:\n')
    print('ssg1 config --title <site title> --url <site url> --author <site author>\n')


def config(args: argparse.Namespace) -> None:
    
    config_data = {}
    if args.title:
        config_data['title'] = args.title
    if args.author:
        config_data['author'] = args.author
    if args.url:
        config_data['url'] = args.url
    if args.email:
        config_data['email'] = args.email
    if args.copyright:
        config_data['copyright'] = args.copyright
    if args.folder:
        config_data['folder'] = args.folder
    if args.lang:
        config_data['lang'] = args.lang
    
    if conf.config_file.exists():
        current_config = load_config()
        current_config.update(config_data)
        config_data = current_config

    save_config(config_data)


def post(args: argparse.Namespace) -> None:

    dt = datetime.datetime.now(datetime.timezone.utc).astimezone()
    post_date = dt.strftime('%Y-%m-%d')
    post_datetime = dt.isoformat(timespec='milliseconds') # ISO 8601

    meta, slug = build_meta(args.title, datetime_str=post_datetime, tag=args.tag)

    post_file = conf.blog_dir / f'{slug}-{post_date}.md'

    write_file(post_file, meta)
    if post_file.exists():
        print(f'Wrote post file to {post_file}')


def page(args: argparse.Namespace) -> None:
    
    nav = load_nav()

    meta, slug = build_meta(args.title)
    
    page_file = Path(f'{slug}.md')

    write_file(page_file, meta)
    if page_file.exists():
        if args.title not in nav:
            nav[args.title] = f'/{slug}/'
        
        save_nav(nav)
        
        print(f'Wrote page file to ./{page_file} and updated nav')


def build(args: argparse.Namespace) -> None:

    md = markdown.Markdown(extensions=['meta'])
    site_config = load_config()
    site_nav = load_nav()

    if not (site_config.get('title') and site_config.get('url') and site_config.get('author')):
        print('error: need to have site title, url, and author configured')
        sys.exit(1)

    site_config['generator'] = f'ssg1 {__version__}'
    site_config['base_path'] = '/'
    folder = site_config.get('folder', False)
    if folder:
        site_config['base_path'] = f'/{folder}/'
        for nav in site_nav.keys():
            site_nav[nav] = f'/{folder}{site_nav[nav]}'

    nav_items = [
        {
            'name'  : nav,
            'id'    : site_nav[nav].split('/')[-2] if nav != 'Home' else 'home',
            'path'  : site_nav[nav]
        }
        for nav in site_nav
    ]
 
    site_config['lang'] = site_config.get('lang', conf.lang)
    site_config['nav_class'] = 'nav-folder' if folder else 'nav-root'
    site_config['nav_idx'] = site_nav
    site_config['nav_list'] = nav_items
    site_config['max_posts'] = site_config.get('max_posts', conf.max_posts)
    site_config['excluded_files'] = [name.lower()
                                     for name in site_config.get('excluded_files', conf.excluded_files)]

    shutil.rmtree(conf.output_dir, ignore_errors=True)
    conf.output_dir.mkdir()
    conf.blog_output_dir.mkdir()
    for in_dir, out_dir in conf.in_out_dir_map:
        if str(in_dir) == 'images' and not any(in_dir.iterdir()):
            continue
        if str(in_dir) == 'blog':
            continue
        shutil.copytree(in_dir, out_dir)

    posts = []
    pages = []

    for post_file in conf.blog_dir.iterdir():
        post_data = render_post(md, post_file, site_config)
        posts.append(post_data)
    
    for page_file in Path('.').glob('*.md'):
        if str(page_file).lower() in site_config['excluded_files']:
            continue
        page_data = render_page(md, page_file, site_config)
        pages.append(page_data)
    
    if posts:
        posts = sorted(posts, key=lambda x: x['datetime_obj'], reverse=True)

    build_tag_indexes(posts, site_config)

    for post_data in posts:
        tag = post_data.get('tag', None)
        slug = post_data['slug']
        post_dir = conf.blog_output_dir / tag / slug if tag else conf.blog_output_dir / slug
        post_dir.mkdir()
        write_index_file(post_dir, post_data['html_page'])
 
    for page_data in pages:
        page_dir = conf.output_dir / page_data['slug']
        page_dir.mkdir()
        write_index_file(page_dir, page_data['html_page'])

    build_blog_index('Blog', posts, conf.blog_output_dir, site_config)
    build_blog_index('Latest Posts', posts[:site_config['max_posts']], conf.output_dir, site_config)
    
    print(f'build finished, posts: {len(posts)}, pages: {len(pages)}')


def serve(args: argparse.Namespace) -> None:
    if not conf.output_dir.exists():
        print(f'no {conf.output_dir} dir found, nothing to serve')
        sys.exit(0)

    os.chdir(conf.output_dir)
    with socketserver.TCPServer(('', args.port), SimpleHTTPRequestHandler) as httpd:
        print(f'serving at http://localhost:{args.port}')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\nstopping server')
            httpd.shutdown()
            httpd.server_close()
            sys.exit(0)


def build_blog_index(title: str, posts: list, dir_path: Path, site_config: dict) -> None:
    blog_template = conf.env.get_template('blog.html')
    rss_template  = conf.env.get_template('feed.xml')

    if str(dir_path) == 'www':
        blog_path = site_config['base_path']
    else: 
        blog_path = site_config['base_path'] + str(dir_path).replace('www/', '') + '/'

    for template, output_type in zip([blog_template, rss_template], 
                                     ['html', 'xml']):

        output = template.render(blog_title=title, blog_path=blog_path, posts=posts, 
                                 posts_len=len(posts), site=site_config)
        
        write_index_file(dir_path, output, output_type)


def build_tag_indexes(posts: list, site_config: dict) -> None:
    template = conf.env.get_template('tags.html')

    tag_index, tags = index_tags(posts)
   
    for tag in tags:
        tag_dir = conf.blog_output_dir / tag
        tag_dir.mkdir()
        
        posts = tags[tag]['posts']
        build_blog_index(f'{tag.lower().capitalize()} Blog', 
                         posts, tag_dir, site_config)
    
    tag_page_dir = conf.output_dir / 'tags'
    tag_page_dir.mkdir()
    tags_html = template.render(tag_index=tag_index, tags=tags, site=site_config)
    write_index_file(tag_page_dir, tags_html)


def index_tags(posts: list) -> tuple:
    tags = {}
    for post_data in posts:
        tag = post_data.get('tag', None)
        if not tag:
            continue
        if tag not in tags:
            tags[tag] = {
                'posts': [post_data],
                'count': 1
            }
        else:
            tags[tag]['posts'].append(post_data)
            tags[tag]['count'] += 1

    tag_index = sorted(list(tags.keys()))
    
    return tag_index, tags


def write_index_file(dir_path: Path, output: str, output_type: str = 'html') -> None:
    index_file = dir_path / f'index.{output_type}'
    write_file(index_file, output)

def render_post(md_obj: markdown.Markdown, post_file: Path, site_config: dict) -> dict:
    
    template = conf.env.get_template('post.html') 
    
    post_data = render_markdown(md_obj, post_file)
    dt = datetime.datetime.fromisoformat(post_data['datetime']) # ISO 8601
    post_data['date'] = dt.strftime('%Y-%m-%d')
    post_data['datetime_obj'] = dt
    post_data['datetime_visual'] = dt.strftime('%a, %d %b %Y %H:%M:%S %z') # RFC 822
    post_data['type'] = 'post'

    html_page = template.render(post=post_data,
                                site=site_config)
    
    return {
        'html_page'         : html_page,
        'path'              : get_page_path(post_data, site_config),
        'datetime_obj'      : dt,
    } | post_data


def render_page(md_obj: markdown.Markdown, page_file: Path, site_config: dict) -> dict:
    
    template = conf.env.get_template('page.html')

    page_data = render_markdown(md_obj, page_file)
    html_page = template.render(page=page_data, site=site_config)
    page_data['type'] = 'page'

    return {
        'html_page' : html_page,
        'path'      : get_page_path(page_data, site_config),
    } | page_data


def get_page_path(meta: dict, site_config: dict) -> str:
    slug = meta['slug']
    path = ''
    is_post = meta['type'] == 'post'
    if is_post:
        path += '/blog/'
        tag = meta.get('tag', None)
        if tag:
            path += f'{tag}/'
        path += f'{slug}/'
    else:
        path = f'/{slug}/'

    folder = site_config.get('folder', False)
    page_path = path if not folder else f'/{folder}{path}'

    return page_path
 

def render_markdown(md_obj: markdown.Markdown, md_file: Path) -> dict:
    
    text = escape(read_file(md_file))
    html = md_obj.convert(text)
    meta = {k: v[0] for k, v in md_obj.Meta.items()}

    return {
        'html': html
    } | meta


def get_slug_from_title(title: str) -> str:

    slug =  title.translate(conf.slug_replace_map).lower()
    if '--' in slug:
        slug_new = ''
        clean_flag = False
        for c in slug:
            if c == '-' and not clean_flag:
                slug_new += c
                clean_flag = True
                continue
            elif c == '-':
                continue
            else:
                slug_new += c
                clean_flag = False

        slug = slug_new

    if slug[0] == '-':
        slug = slug[1:]
    if slug[-1] == '-':
        slug = slug[:-1]

    return slug


def build_meta(title: str, datetime_str: str = None, tag: str = None) -> tuple:
    slug = get_slug_from_title(title)
    meta = f'---\ntitle: {title}\nslug: {slug}\n'
    if datetime_str:
        meta += f'datetime: {datetime_str}\n'
    if tag:
        meta += f'tag: {tag}\n'
    meta += f'---\n\n\n'
    
    return meta, slug
        

def load_config() -> dict:
    
    config_data = read_file(conf.config_file)
    
    return json.loads(config_data)


def save_config(config_data: dict) -> None:
    write_file(conf.config_file, json.dumps(config_data, indent=4))
    

def load_nav() -> OrderedDict:
    
    nav_data = read_file(conf.nav_file)

    return json.loads(nav_data, object_pairs_hook=OrderedDict)


def save_nav(nav_data: OrderedDict) -> None:
    write_file(conf.nav_file, json.dumps(nav_data, indent=4))


def write_file(file_path: Path, content: str) -> None:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def read_file(file_path: Path) -> str:
    if not file_path.exists():
        print(f'error: ({file_path}) not found')
        sys.exit(1)

    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def parse_args(args: list = None) -> argparse.Namespace:
    
    root_parser = argparse.ArgumentParser(prog='ssg1')
    root_parser.add_argument('-v', '--version', 
                        action='version', version=f'%(prog)s {__version__}')

    subparsers = root_parser.add_subparsers(title='commands', dest='cmd')
    
    init_parser = subparsers.add_parser('init')
    config_parser = subparsers.add_parser('config')
    for parser in [init_parser, config_parser]:
        parser.add_argument('-t', '--title', type=str, help='Site title')
        parser.add_argument('-u', '--url', type=str, help='Site URL')
        parser.add_argument('-f', '--folder', type=str, help='Site base path folder')
        parser.add_argument('-a', '--author', type=str, help='Site author')
        parser.add_argument('-e', '--email', type=str, help='Site email')
        parser.add_argument('-c', '--copyright', type=str, help='Site copyright year(s)')
        parser.add_argument('-l', '--lang', type=str, help='Site language (rfc 1766)')

    post_parser = subparsers.add_parser('post')
    post_parser.add_argument('title', type=str, help='Post title')
    post_parser.add_argument('-t', '--tag', type=str, help='Post tag')
    
    page_parser = subparsers.add_parser('page')
    page_parser.add_argument('title', type=str, help='Page title')

    build_parser = subparsers.add_parser('build')

    serve_parser = subparsers.add_parser('serve')
    serve_parser.add_argument('-p', '--port', type=int, help='Server port', default=8000)

    return root_parser.parse_args(args)


def main() -> None:

    args = parse_args()
    if not args.cmd:
        parse_args(['-h'])

    commands = {
        'init'  : init,
        'config': config,
        'post'  : post,
        'build' : build,
        'page'  : page,
        'serve' : serve,
    }

    commands[args.cmd](args)


if __name__ == '__main__':
    main()

