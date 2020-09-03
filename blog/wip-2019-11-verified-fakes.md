---
tags: python, testing, TDD, case-study, pytest
title: Verified Fakes: Best of Both Worlds
published: 10th of November, 2019
tagline: >
  Get fast feedback and be confident you're testing the right thing 

---

# Why do we write tests?

To prove that the software is correct? Sure they increase confidence, but tests don't prove the code
is "correct" in all ways, they just show that for the specific senarios tested the code behaves as
expected.

To prevent regressions? This is a major benefit. There's a certain comfort when joining an existing
project in knowing that if you've made a change and the tests still pass, you probably did not break
a bunch of features you did not even know exist.

There are many reasons to do it, but for me it's about having a **fast feedback loop**. For
the feedback loop to be fast, tests need to be fast. So what do we do when we have to test
something that calls out to external services and is inherently slow?  Why we use mocks,
fakes, etc.

This is about how we got such a fast feedbak loop while maintaining confidence in our test
suite, in a project called Zinc. Zinc is an open source DNS zone manager for Route53 and was
developed at an awesome little Wordpress hosting company called Presslabs.

# An example project: Zinc

Zinc's main purpose is keeping DNS up to date using AWS's Route53 API. If a customer sets up
a new site, Zinc would have to know about it, and create the matching DNS entries. If one
of our CDN servers would be taken down for maniatance or went offline, Zinc would have to
update hundreds of zones for all customers who's traffic was served by that machine.

# Detour: More on Zinc

Skip this if you're just curious about the tests

Zinc filled a very specific need at Presslabs: Geographic Load Balancig

When someone looks up the domain for a client's site, we want them to get back the IP of a
geographically close CDN server, for low latency. AWS already provides Policy Routed Records for
this, but at a price that would make it hard to justify for your average Wordpress site in search of
hosting. But, the building blocks of these Policy Routed Records are available in the Route 53 api
so anyone can roll their own. That's what Zinc is DIY roll-your-own policy routed records using
Route53.

# How do we go about testing this?

We could use Route53 and some dedicated test credentials.

Unfortunatelly that would be slow, and would also introduce bariers to new collaborators. If you're
a new dev in the company we'll need to make sure you get a copy of the credentials. And for folks
outside the company just interested in contributing a patch, realistically it would probably mean no
one would really run the test, and that would be a shame. Remember tests aren't there to prove the
software is defect free, they're there to make the development experience nicer by providing a
near-instant feedback loop.

The most common approach seems to be, a small number of integration tests focusing mostly
on happy path, and a larger base of unittests that rely on mocks. This way most tests stay
fast, but you have some confidence your code works with the real thing.

That's ok, but I find that sometimes the mocks fall out of sync with the real thing and I
end up with obtuse tests that "assert some function was called with a long list of
arguments". 

What I really want are tests that look like this:

 * given this initial state
 * and this target state
 * run my code
 * and assert the new state matches the target state

# Fakes

A fake is not a mock. Unlike a mock which we just set up to return well-known values when calling
it's methods, a fake should be a toy implementation of the interface of the real thing. So if I
create a zone then fetch the list of zones I should see the effects of my interaction.

It might sound like a lot of work but the upside of using Python is we only have to implement the
subset of the interface we actually use (duck typing has it's upsides).

# Ok, so how do I make sure my Fake actually behaves

The approach for Zinc: let's run the same tests with both boto3 and a fake. This way I can use
the fake most of the time, but if I suspect some issue only happens with the real thing, I
can quickly confirm that suspicion by running the tests agains the real thing as well.

That's it, really. If that seems like an obvious idea, it sort of is as pleny of people seem to have
stumbled upon it. The only name I've so far seen for the pattern is "verified fakes". While I don't
think it's an ideal name, I'm gonna use it so we don't 

# Detour: pytest's parametrized fixtures

Since all I want is to run the same tests multiple times, once with a fake and once with
boto, this sounds like a job for pytest's parametrized fixtures.

```
@pytest.fixture(
    params=[
        # our fake
        Moto,

        # the real client, wrapped in a class wich will add a cleanup so tests are fully
        # isolated when using the route53 API
        lambda: CleanupClient(route53.client.get_client()),
    ],
    ids=['fake_boto', 'with_aws']
)
def boto_client(request):
    client = request.param()
    patcher = patch('zinc.route53.client._client', client)
    patcher.start()

    def cleanup():
        patcher.stop()
        client.cleanup()
    request.addfinalizer(cleanup)
    return client

```

And just like that any test that requires the boto_client fixture will get executed twice. 

Spoiler alert, I am a huge han of pytest and fixture parametrization is one it's best features.
