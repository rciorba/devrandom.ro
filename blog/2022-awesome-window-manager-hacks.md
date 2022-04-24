---
tags: awesomewm, linux, desktop
title: My Awesome AwesomeWM Hacks
published: 24th of April, 2022
tagline: >
  Smoother handling of adding and removing monitors + virtual screens.
---

# My AwesomeWM Hacks

I've been using AwesomeWM as my daily driver for quite a number of years, but short of minor alterations, like a few custom shortcuts or setting different default layout for each tag, I never really did much to leverage its flexibility until now.

I had a couple of itches I wanted to scratch:

 * Dis-connecting and re-connecting displays are destructive operations: every window from every tag from the removed display, gets moved to the first tag of the remaining display, and when the display is reconnected, they don't "pop back into place".
 * I got an ultra-wide monitor and I'd like to be able to split the display as if they were two virtual monitors, each with their own set of tags.

In this post I will describe solutions to the above problems.

**N.B.** the code in this post was tested with AwesomeWM compiled from git master. Several things have changed since the 4.3 release, especially around handling how screens are added and removed, so if you'd like better multi-monitor support you probably should upgrade from 4.3.
The code also assumes awesome is started with the "screen=off" option, see the [docs on modelines](https://awesomewm.org/apidoc/documentation/09-options.md.html).


**Disclaimer:** I'm no expert on AwesomeWM so take my descriptions its internal workings with a huge grain of salt, these are just my observations from a bit of hacking around.


# Restore windows to their original screen and tag, once display is reconnected

**N.B.** The following "solution" assumes you have identically named tags across screens, and I haven't tested it for windows mapped to multiple tags.

By default, disconnecting a screen moves all windows from all tags to the first tag of the other screen.
I'd prefer a "merge" type behaviour, where the windows on the removed screen become secondary<sup>[<a href="#fn-1">1</a>]</sup> windows on the equivalent tag of the remaining screen. This works well for me, as I always have the same number of tags on both screens, and I use the same tag for the same activity (Emacs on one screen's tag 3, and a terminal with tests on the other screen's tag 3), so I would prefer my tests terminal to stay on tag 3 when I unplug a monitor. And finally, when I do re-connect the second screen, I'd like the tests terminal to move back to tag 3 of the re-connected monitor.

This one turned out to be simple (once I had a better understanding of the WM events).

 * `tag.request::screen` is fired for each tag when a screen is about to be removed, giving it the opportunity to cleanup (find a new screen and tag) for every window. The default handler simply picks the first tag, but we're going to look for a tag with the same name, and also store the index of the current screen on the window object itself(the preferred screen), so we can restore it later.
 * `screen.added` - this was a trap. It felt like the "correct" event, but this is fired before the screen has been initialized (i.e. before tags were created for it), so restoring failed and it took me a while to figure out the cause.
 * `screen.request::desktop_decoration`. This one feels like a hack, as it seems intended for setting up the screen, but given the default handler for this initializes the tags, I added my window-restoring logic here, and it works like a charm.



```lua
-- Handle screen being removed.
-- We'll look for same tag names and move clients there, but preserve
-- the "desired_screen" so we can move them back when it's connected.
tag.connect_signal("request::screen", function(t)
    local fallback_tag = nil

    -- find tag with same name on any other screen
    for other_screen in screen do
        if other_screen ~= t.screen then
            fallback_tag = awful.tag.find_by_name(other_screen, t.name)
            if fallback_tag ~= nil then
                break
            end
        end
    end

    -- no tag with same name exists, use fallback
    if fallback_tag == nil then
        fallback_tag = awful.tag.find_fallback()
    end

    if not (fallback_tag == nil) then
        clients = t:clients()
        for _, c in ipairs(clients) do
           c:move_to_tag(fallback_tag)
           -- preserve info about which screen the window was originally on, so
           -- we can restore it if the screen is reconnected.
           c.desired_screen = t.screen.index
        end
    end
end)
```

This is the code which will restore windows back to their desired screen:

```lua
function restore_windows_to_desired_screen(new_screen)
    for _, c in ipairs(client.get()) do
       if not (c.desired_screen == nil) then
          tag_name = c.first_tag.name
          c:move_to_screen(c.desired_screen)
          tag = awful.tag.find_by_name(c.screen, tag_name)
          if not (tag == nil) then
             c:move_to_tag(tag)
          end
          -- now clear the "desired_screen"
          c.desired_screen = nil
       end
    end
end
```

Now, we have to call `restore_windows_to_desired_screen`. In the default AwesomeWM config, we have a handler for `screen.request::desktop_decoration` and this is where everything is setup for the new screen (tags, the taglist widget, the tasklist widget, the top bar, etc). As our restore code looks for tags of the same name on the newly connected screen, we can only run it after we initialized the tags, so let's do just that:

```lua
screen.connect_signal("request::desktop_decoration", function(s)
    -- Each screen has its own tag table.
    awful.tag({ "1", "2", "3", "4", "5", "6", "7", "8", "9" }, s, awful.layout.suit.tile)
    -- Call our restore function, now that tags are setup
    restore_windows_to_desired_screen(s)
    ...
```

That's kind of it.

Also, thanks to [bodograuman for sharing their window restoring code](https://github.com/awesomeWM/awesome/issues/1382#issuecomment-430909577), as it served as an inspiration and starting point for me.

# Virtual displays

More cool stuff: my ultra-wide monitor provides about as much screen real-estate as one and a half monitors. I've been able to tweak things to the point where I have 2 virtual screens with roughly a 3/4 and 1/4 split. I can also resize them on the fly and switch to a single screen layout easily. This is relatively easy to pull off given AwesomeWM offers: [fake\_add](https://awesomewm.org/apidoc/core_components/screen.html#fake_add), [fake\_remove](https://awesomewm.org/apidoc/core_components/screen.html#fake_remove), and [fake\_resize](https://awesomewm.org/apidoc/core_components/screen.html#fake_resize) out of the box.

This is a great productivity booster for me:

 * I tend to use the "second screen" when coding, to run tests as soon as I've changed the code.
 * Sometimes I move a current call to the second screen, and use the "main screen" to look up relevant information. I find 2 virtual screens makes this a lot easier, as I can still use my regular window-manager flow (tile windows, jump between tags) on the "main screen" while the call stays in place on the "second".

My workflow is not fancy: I want either the vanilla "each monitor == one screen" or "exactly one monitor == 2 screens" (what I use on the ultra-wide monitor 95% of the time). Also I want to be able to switch between the two.

Here's what the split layout looks on a 3440x1440 display:
![split layout](img/2022-awesome-split.jpg)


## Adding a fake screen
Switching from a single screen to a split layout means resizing the one existing screen and adding a fake. The below code does a bit more than that, it also tracks "fakes" and the original dimensions of the "real" screen, and we will see later how we use that information when we handle removing the fake and returning to a non-split layout.


```lua
local function wide_split_layout()
   if (screen.count() ~= 1) then
      -- A sanity check, so we don't split multiple times.
      debug("more than 1 screen, bailing on wide_split_layout", screen.count())
      return
   end
   local geo = screen[1].geometry
   local new_width = math.ceil(3*geo.width/4) - 30  -- personal sweet spot for main screen size
   local new_width2 = geo.width - new_width
   local parent = screen[1]
   parent.original_w = geo.width
   parent.original_h = geo.height
   parent:fake_resize(geo.x, geo.y, new_width, geo.height)
   fake = screen.fake_add(geo.x + new_width, geo.y, new_width2, geo.height)
   if (parent.fakes == nil) then
      parent.fakes = {}
   end
   parent.fakes[fake.index] = fake
   for k, v in pairs(fake.tags) do
      v.layout = awful.layout.suit.tile.bottom
   end
   collectgarbage('collect')
end
```

## Removing the fake screen

Now for switching back to the regular (non-split) layout. It's quite simple, we need to:

 * look for "parent" screens and remove all their "fakes"
 * resize the "parent" back to its original width


```lua
local function non_wide_layout()
   for s in screen do
      if s.fakes then
         for _, f in pairs(s.fakes) do
            f:fake_remove()
         end
         s.fakes = nil

         local geo = s.geometry
         s:fake_resize(geo.x, geo.y, s.original_w, geo.height)
      end
   end
end
```

## Dealing with displays being resized

As an aside, handling X11 displays (which one is primary, changing resolutions, etc) isn't the responsibility of the window manager. I run xfsettingsd (from xfce4) and also have a few layouts scripts created using arandr, for those few times when plugging in a display doesn't "just work".

Back to handling resize events. I'm not 100% sure how awesome numbers the screens or how it manages them. My observation has been that screen 1 is always my primary X11 monitor. 

Some examples:

 * When I attach a display it becomes my new primary. While this looks like adding a new screen and moving stuff over to it, what actually happens is: screen 1 is moved to a new display and resized, and screen 2 is added. Similarly when I unplug the monitor: screen 2 gets removed, and screen 1 is moved to the other output and resized.
 * With my ultra-wide I actually disable the laptop screen and use the external monitor exclusively. This means no screens are added or removed, and screen 1 is resized. When combined with restoring the split fake screen back to it's original size, I had a bug where my "go back to non-split layout" code would restore the size of the old display not the new one :)

With this in mind we need to update the "original width" to match the resized display, and while we're at it let's try to be "clever" and go to either split or unsplit layout based on the new size of the display:

```lua
screen.connect_signal(
   "request::resize",
   function(old, new, reason)
      -- Update "original size" to match the resized display.
      for s in screen do
         if (s.original_w == old.geometry.width) and (s.original_h == old.geometry.height) then
            s.original_w = new.geometry.width
            s.original_h = new.geometry.height
         end
      end

      -- Some extra convenience: go to prefered layouts depending on the size.
      if new.geometry.width == 3440 then
         -- We seem to have connected the extrnal ultra-wide.
         wide_split_layout()
      end
      if new.geometry.width == 1920 then
         -- We seem to have transitioned to the laptop screen.
         non_wide_layout()
      end
end)
```

I admit tracking and updating the screen's original size this way feels quite hacky, but it works so I don't have the motivation to look for a more elegant solution :)


## Resizing the fake screens

Now let's add the ability to adjust the size of the fake screens.

```lua
local function resize_fake_screen(delta)
   if (screen.count() ~= 2) then
      -- sanity check
      return
   end
   local geo1 = screen[1].geometry
   local geo2 = screen[2].geometry
   screen[1]:fake_resize(geo1.x, geo1.y, geo1.width+delta, geo1.height)
   screen[2]:fake_resize(geo2.x+delta, geo2.y, geo2.width-delta, geo2.height)
end
```

## Keybindings

And let's tie it all together with keybindings for the above. My keybindings are:

 * F5 - make parent screen narrower and widen the side screen
 * F6 - go to single screen layout
 * F7 - go to split screen layout
 * F8 - make parent screen wider and side screen narrower

```lua
globalkeys = gears.table.join(
    globalkeys,
    awful.key({ modkey,           }, "#72",   function() non_wide_layout() end,
              {description="single screen layout", group="layouts"}),
    awful.key({ modkey,           }, "#73",   function() wide_split_layout() end,
              {description="wide screen split layout", group="layouts"}),
    awful.key({ modkey,           }, "#71",   function() resize_fake_screen(-15) end,
              {description="resize screen -15", group="layouts"}),
    awful.key({ modkey,           }, "#74",   function() resize_fake_screen( 15) end,
              {description="resize screen +15", group="layouts"}),
)
```


# Debugging tips

## Print-debugging and capture AwesomeWM's output

It took me some trial and error to get the code here working. I was asking myself questions such as "did I mess up tracking the desired screen when removing the screen, or did I mess up restoring the tag when a screen is added?". Being able to add some well placed prints helps you narrow it down.

If you're using lightdm the .desktop file won't let you do output redirection, but you can create a wrapper script and exec that.

Here's how my `/usr/share/xsessions/awesome.desktop` looks like:

```ini
[Desktop Entry]
Name=awesome
Comment=Highly configurable framework window manager
TryExec=awesome
Exec=awesome-dbg
Type=Application
Icon=/usr/share/pixmaps/awesome.xpm
Keywords=Window manager
```

And `/usr/local/bin/awesome-dbg`, the wrapper script to do output redirection:

```sh
#!/bin/sh

exec awesome "$@" > ~/.awesome-dbg
```
Now you can sprinkle `print("text")` and `gears.debug.dump(obj, "text")` anywhere you see fit and tail `~/.awesome-dbg`.

## Don't break your desktop, use nested X while hacking

In order to avoid breaking your config and being unable to use your computer, it's really nice to be able to start another instance of AwesomeWM while you hack away on the config. This is easy to pull of by using Xephyr to start a nested X session:

```fish
Xephyr -ac -screen 3430x1380 :99 &
set -x DISPLAY :99
# if you haven't embraced the fish shell yet:
# export DISPLAY=:99
awesome -c ~/path/to/rc.lua
```

# Closing
Oh wow, I can't believe you made it this far! If you have thoughts or suggestions please share them on the [reddit thread](https://www.reddit.com/r/awesomewm/comments/ubfjxo/restoring_windows_when_a_screen_is_reconnected/).

Also, my [full AwesomeWM config is on github](https://github.com/rciorba/misc/blob/master/awesome/rc.lua), but it's probably harder to read than to go through the code in this post.

<hr>
Footnotes:

[<a id="fn-1">1</a>] the AwesomeWM layouts and APIs still use a "master"/"slave" terminology, which nowadays might be considered... out of touch.
