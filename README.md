# ⚠️ Better Control – Development Branch

> [!WARNING]
>  You are on a **highly experimental branch**.  
> Nothing here is stable. Nothing is guaranteed.  
> Only touch this if you are a **developer**.

## About

This branch is **under active development**.  
Expect broken code, missing features, and chaos.  

- Wi-Fi module: probably broken  
- Volume module: might crash  
- Everything else: who knows?  

> [!IMPORTANT]
> TL;DR: This is **NOT** for installation or casual use.

## How to build

```bash
git clone https://github.com/better-ecosystem/better-control.git
cd better-control
git checkout c-rewrite

meson setup builddir
meson compile -C builddir
./target/better-control
```
