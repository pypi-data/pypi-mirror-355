# PubCrank CLI

Static site generator.

## Install

`pipx install pubcrank-cli`

## Usage

`pubcrank build -c mysite/pubcrank.hjson`


### File Layout

```
mysite/pubcrank.hjson

mysite/assets:
favicon.ico    favicon-16x16.png    favicon-32x32.png
manifest.json  img/

mysite/content:
about.md  blog/  index.md

mysite/themes:
plain/
```

### Configuration

```hjson
{
  site: {
    name: Example Site
    nav: [
      {name: "Home", url: "/"}
      {name: "Blog", url: "/blog/"}
      {name: "About", url: "/about.html"}
    ]
  }
  theme: "plain"
}
```
