---
tags: home-network, fun, odroid, syncthing, linux
title: My private "cloud/backup" setup.
published: 2th of March, 2022
tagline: >
  A love letter to Syncthing.

---

# My "Cloud/Backup" Setup & Future Plans

## TL;DR: Current Setup

The devices:

 * 2 laptops (Linux), running Syncthing.
 * 2 Android phones (mine and my girlfriend's), running syncthing-android
 * 2 XU4 Odroids (Linux) + Cloud Shell, one working and another finally "fixed" and almost
   setup. Again, using Syncthing.
 
The experience is Dropbox-like, local data is kept in sync between multiple devices. This is great
as I want access to this data even when I don't have an internet connection. The setup is:

 * My phone's photos are replicated to the Odroid and both laptops (finally no more Google Photos).
 * A "shared" photo album between our phones and the Odroid so I don't have to send photos over
   WhatsApp, one batch at a time. I can just use my phone's gallery app, and Copy/Move photos to an
   album and presto.
 * A document "shared directory" between all devices.
 * Misc shares as needed (I use one between the odroid and both laptops to seamlessly switch between
   the 2 laptops without having to git commit,push,pull)

That's really it, it kinda "Just Works&#8482;", using Syncthing and syncthing-android.


## To Do: Backups

For now I don't really have a good backup story. My data is indeed replicated but a deletion or
accidental modification on one device will be propagated to all, and that needs addressing next. I
intend to use btrfs snapshots for that.

I see 2 options for replication between Odroids:

 1. replication via Syncthing and have each device do incremental snapshots
 2. one Odroid will be a "primary" and replicate its snapshots to the secondary
 
I'm leaning toward option 1 as it would have several benefits:

 * fewer moving parts, all replication happens via Syncthing everywhere (btrfs send/recv would
   require Odroids setup to be able to ssh to each other)
 * more resilient as I can backup to any odroid. Alternately if the "primary" were to fail I'd not
   have backups anymore until I fix it or somehow transform the replica to a primary.
   
## Hardware
I'm quite pleased with the XU4, and the Cloud Shell 1 is nice (it's been
[supplanted](https://www.hardkernel.com/shop/cloudshell2-case2-for-xu4-smokyblue/)). The only
"issue" was a noisy fan which [I replaced with a
Noctua](https://forum.odroid.com/viewtopic.php?t=23669), and "silenced" slightly by [tweaking the
fan speed settings](https://www.hardkernel.com/blog-2/how-to-control-odroid-xu4-cooling-fan/). I
personally chose a setup where the fan never stops as the constant on/off is annoying. I found
spinning the fan as slow as possible maintains enough air-flow that it doesn't often have to spin
up. The only "pitfall" was that the fan won't start at very low speed. This is easy to tweak with a
script that manually sets the speed to 100% for a few seconds before switching to auto fan control
with a very low speed for the first temperature threshold.

Odroid has recently released the HC4 which has 2 SATA ports and looks really promising for these
sort of DIY NAS projects. If I were starting this project today I think it would be my first pick.

The XU4Q (passive cooling version) is also probably a nice choice if you're going for a custom
case. Paired with a larger and quieter case fan, this would also make for a nice solution.

A PI4 is also probably a good choice. I'm curious if its 4 GB of RAM give it an edge over the the
XU4 and its 2GB.

# The Long Procrastinated Journey

## Initial Plans for Backup, Using BorgBackup

My initial plan (2017, what can I say I'm a very effective procrastinator) was to use BorgBackup
for some of the data on my laptop. At the time the Android story wasn't as important to me. For
hardware I chose an Odroid-XU4, as it packed more computing umphf than the Pi 2 and had a gigabit
Ethernet port which, unlike the Pi's 100mbit Ethernet port, didn't share the USB bus with the USB
ports which will have to handle the disk's IO.

I bought 2 Odroid (and cloud shells to accommodate HDDs) and was planning doing either of:

 * Laptops -> Primary Odroid -> Replica Odroid
  * laptops use BorgBackup to backup to Odroid1
  * Odroid1 replicates data somehow to Odroid2 (btrfs snapshot send/recv maybe)

 * Laptops -> Both Odroids, in turn
  * laptops use BorgBackup to backup to Odroid1
  * laptops use BorgBackup to backup to Odroid2

See BorgBackup's [FAQ for
advice](https://borgbackup.readthedocs.io/en/stable/faq.html#can-i-copy-or-synchronize-my-repo-to-another-location)

Hardware purchased and Odroid set up, procrastination kicked in (I'm supposed to say that "life got
in the way" but despite the end of a long-term relationship, the start of a new long-term
relationship, being laid off, finding a new job twice and emigrating... I was probably really just
procrastinating).

## Re-assessing the Android Story

Google Photos has been extremely convenient to use, but I had been feeling very uneasy about how much
access Google has to my data. In addition moving documents between my phone, personal laptops and
work laptop became an increasingly frequent chore. I would check-in for a flight on a laptop, get a
PDF with a bar-code which I'd have to somehow transfer to my phone (email usually). It would be great
to save a file to some directory and just have it on all devices.

At some point I heard of Syncthing, and gave it a spin, and I just loved it. It works well on
Android, at least for me as I don't have an [SD
card](https://github.com/syncthing/syncthing-android/wiki/Frequently-Asked-Questions#what-about-sd-card-support).

# Closing thoughts

So yeah, I don't wanna knock BorgBackup, it's really great software and if you're just looking for a
an incremental, deduplicating, enctypted backup solution you really should check it out.

The sort of experience offered by Syncthing is great for me and pairing that with FS snapshots
should make for a great solution for my phone's photos, and my workflows in general.

If a private Dropbox sounds good to you, try Syncthing out, and if you feel it brings you joy (like
any well working tool that does its job and gets out of your way should), consider
[donating](https://syncthing.net/donations/).

<p class="postscript">This post was mostly written on the 30th of December 2021.</p>
