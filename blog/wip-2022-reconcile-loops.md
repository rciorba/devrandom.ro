---
tags: architecture, fault-tolerance, django, celery
title: Don't fire and forget celery tasks, use a reconcile loop instead
published: 10th of April, 2023
tagline: >
  So how many times should your Celery Task retry? If it gives up, will your system be fine?

---


If you're an experienced developer this post might seem like common-sense, but experience has thought me common-sense advice is worth repeating.

Also, I'm gonna be using Celery as an example, but it applies to any system where you can offload work to a different system to excute, tipically by using a message queue.

# So you're doing something slow during handling of an HTTP request

This is the starting point for most people's journey into the world of Task Queues: you need to perform a time-consuming operation during the handling of an HTTP request. Maybe you need to speak to an external system, which can be slow (the user deleted a site from your dashboard and you need to call AWS to update some DNS records). Maybe you need to do something computationally expensive (the user just uploaded a photo and you need to re-size it). No matter the action, the slowness is an issue for several reasons:

 * the UI feels laggy
 * requests can time-out (you don't have as much control as you think over this timeout)
 * your webserver probably has a limited worker pool, and a few requests to a slow endpoint can exhaust the worker-pool (heck, sometimes bad actors will deliberately bombard your slowest endpoints with requests for a Denial of Service attack)
 
If you've been in a situation like the above, you might have reached for a Task queue.

# Tasks and eventual consistency. No, we're not talking about some fancy-schmancy 2010s NoSQL DB here.

What's this about "eventual consistency"?

When your 100% of your busyness-logic executed in the request-response cycle (on your web-server), you had a pretty simple way to ensure data-integrity: db transactions.

Client asks us to delete a DNS record:
 * begin transaction
 * delete the record in the DB
 * update AWS
 * commit transaction

If the "update AWS" step fails, we can rollback the transaction, leaving the system in a correct state (our DB, and the external system are in sync).

If you think hard enough about this, you know there's a chance for this to go wrong. It is possible that the update to the external system goes through, but something else causes our code to fail and the transaction to never commit (maybe the server was )
