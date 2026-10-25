# ssg1

Minimalist and pragmatic static site generator, with an emphasis on blogging.

## Requirements

Python 3.13+

## Dependencies

* [Jinja2](https://pypi.org/project/Jinja2/)
* [MarkupSafe](https://pypi.org/project/MarkupSafe/)
* [Markdown](https://pypi.org/project/Markdown/)

## Features
* Site pages
* Blog posts with optional tags
* RSS feeds

## Install

```shell
git clone https://github.com/joetorx/ssg1.git
cd ssg1
./install.sh
```

The installation script will create a venv under `$HOME/.ssg1`, install dependencies,
copy everything from the `assets` folder, and copy the `bin/*` scripts to `$HOME/bin`.

Ensure that `$HOME/bin` is in your PATH.

## Usage

### Initialize the site

```shell
mkdir wwwsite
cd wwwsite
ssg1 init
```

### Add site configurations

```shell
ssg1 config -t <Site title> -u <Site url> -a <Site author> -e <Site email>
```
The same configs can be passed when doing `ssg1 init`

See more config options with `ssg1 config -h`

### Add a page

```shell
ssg1 page <Page title>
```

After this you can start writing your page content in the generated Markdown file.

### Add a post

```shell
ssg1 post <Post title> -t <category tag>
```

After this you can start writing your post content in the generated Markdown file.

### Build the site

```shell
ssg1 build
```

### Preview the site locally

```shell
ssg1 serve
```

## License

Licensed under the MIT License. See the file LICENSE for details.
