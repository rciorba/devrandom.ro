---
tags: linux, desktop, short, howto
title: Quick howto: fix missing keyboard layout in Xfce settings.
published: 24th of November, 2022
tagline: >
  When setxkbmap lets you set layouts which aren't listed in Xfce's keyboard settings.
---

This is not a deep-dive into how keyboard layouts are configured. This is just a "note to self" in case I ever wonder "how the hell did I fix that"?

The problem: my prefered keyboard layout doesn't show up in Xfce's keyboard settings tool.
`setxkbmap ro basic` works, but gets reset after a while.

The solution: edit `/usr/share/X11/xkb/rules/evdev.xml`. Find the Romanian language section. On Xubuntu 22.04 it looks like this:

```xml
<layout>
  <configItem>
    <name>ro</name>
    <!-- Keyboard indicator for Romanian layouts -->
    <shortDescription>ro</shortDescription>
    <description>Romanian</description>
    <languageList>
      <iso639Id>ron</iso639Id>
    </languageList>
  </configItem>
  <variantList>
    <variant>
      <configItem>
        <name>std</name>
        <description>Romanian (standard)</description>
      </configItem>
    </variant>
    <variant>
      <configItem>
        <name>winkeys</name>
        <description>Romanian (Windows)</description>
      </configItem>
    </variant>
  </variantList>
</layout>
```

Modify the `variantList` to include the following:
```xml
<variant>
  <configItem>
    <name>basic</name>
    <description>Romanian (basic)</description>
  </configItem>
</variant>
```

That's it. "Romanian (basic)" will now show up in the available layouts.
