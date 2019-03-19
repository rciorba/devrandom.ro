---
tags: elixir, Erlang
title: Elixir first impressions
published: 11th of March, 2019
tagline: >
  Thoughts and first impressions as I'm diving in to Elixir.

---

# Elixir first impressions

I'm going to write down my thoughts on Elixir as I'm learning the language, mostly to
cement what I'm learning, and to be able to refer to these notes later.

Where am I coming from? I have some Erlang knowledge and, as I'm diving in to Elixir, I
find myself looking for the similarities (there are obviously many) and the differences.
Also, I should state that all my assumptions are shaped (sometimes without me even
realizing it) by over 10 years of Python.

So let's get to it. This post will include some code examples. The code should be simple
and self explanatory. The only construct I feel needs an introduction is the function
capturing operator `&`.

It can be used to quickly make an anonymous function(what we'd call a fun in Erlang) out
of a function.

```iex
iex(3)> &is_atom/1
&:erlang.is_atom/1
```

Equivalent in Erlang:
```erlang
2> fun erlang:is_atom/1.
fun erlang:is_atom/1
```

In elixir `&` can be used as a shortcut for creating anonymous functions:
```iex
iex(4)> &(&1 * 2)
#Function<6.128620087/1 in :erl_eval.expr/5>
```

# The good stuff

## Structs

Basically just Maps, but with a declared structure. Unlike regular maps that would allow
one to add any key, [Structs](https://elixir-lang.org/getting-started/structs.html)
enforce their structure. Those familiar with how Erlang records are built on top of tuples,
will see a similarity in how Structs are built on top of Maps.

I've felt the need for something like this in Erlang when I had used a map as config for
an application. I had a bunch of very hard to debug test failures because I had
miss-configured the app, but I hadn't checked upfront if everything in the config was OK. I
ended up writing some check code myself and, reading about structs, I think they would
have been a perfect fit for my problem.

## Strings
Ages ago Erlang was notorious for it's poor handling of strings. Thankfully Erlang has
gotten better at this, and now using binaries as strings is the preferred approach. Elixir
embraces the binary string and makes the syntax less cumbersome.

Binary strings no longer need 3 characters to open, and another 3 to close.
```iex
iex(1)> "a"
"a"
iex(2)> <<"a">>
"a"
```

[Read more about Strings](https://elixir-lang.org/getting-started/basic-types.html#strings)

Because compatibility with Erlang is important, the classic Erlang string (which is a
list of integers) is also available. In Elixir it's called a charlist.

Charlists, classic Erlang strings:
```iex
iex(3)> 'A'
'A'
iex(4)> [65]
'A'
```

The only problem I can see is that having both type of strings could be confusing for
people who come to Elixir without knowing the history of Erlang, especially since it's
only a single vs double quote that differentiates them visually.

## Enumerables
Implement the
[Enumerable](https://elixir-lang.org/getting-started/enumerables-and-streams.html#enumerables)
interface... mea culpa, we're supposed call it a protocol...

So implement this protocol and your data type can be used with the Enum module, which
implements common operations like sort, filter, map, reduce, etc.

Here's an example:
```iex
iex(6)> Enum.sum(
...(6)>   Enum.map(0..2, &(&1 * 2))
...(6)> )
6
```

I can't get in to the details of this, because I've only skimmed the surface, but I like
that there's a way to implement your own collections, that compose well with the rest of
the language.

## Ranges
A [Range]() is a sequence of ascending or descending consecutive integers. Very much like
Python's range, only you can't specify a custom step. They're efficient because only the
start and end are stored in memory. Ranges are Enumerable.

## Streams
As the name suggests
[Streams](https://elixir-lang.org/getting-started/enumerables-and-streams.html#streams)
provide a way to stream data one item at a time. You can think of them like UNIX
pipes. Sadly Elixir's pipe operator (`|>`) might resemble pipes, but it's just syntactic
sugar for composing function calls. So while they look similar, unlike pipes data is not
passed to the next function as soon as it's available, but it's passed when the function
completes execution.

Let's write a small data transformation pipeline. We want to take a sequence of numbers,
double each number, then sum them.

The following:

```elixir
Enum.map(0..2, &(&1 * 2)) |> Enum.sum()
```

is just syntactic sugar for:
```elixir
Enum.sum(
    Enum.map(0..2, &(&1 * 2))
)
```

Let's have a closer look at `Enum.map`. It builds and returns a new list.

```iex
iex(4)> Enum.map(0..2, &(&1 * 2))
[0, 2, 4]
```

Let's go back to our pipeline, and add `IO.inspect()` in the middle. It will echo anything
passed to it, then return it, which is perfect for sneaking a peek at what's passing
trough.

```iex
iex(12)> Enum.map(0..2, &(&1 * 2)) |> IO.inspect() |> Enum.sum()
[0, 2, 4]
6
```

Looking at the full example, notice how `Enum.sum` is only called at the very end, once
`Enum.map` has built a new list and returned it. Wouldn't it be nice if we didn't have to
build up the whole list, but rather pass along a partial result as soon as we've processed
one element? If you're familiar with Python this is where you'd use a generator (the yield
keyword was one of the things that made me love Python when I first learned it).

OK back to Elixir. Let's look at using a Stream.

```iex
iex(17)> Stream.map(0..2, &(&1 * 2))
#Stream<[enum: 0..2, funs: [#Function<49.131689479/1 in Stream.map/2>]]>
```

The Stream module provides tools to implement lazy composable data pipelines.
Let's change our example to use Streams:

```iex
iex(14)> Stream.map(0..2, &(&1*2)) |> IO.inspect() |> Enum.sum()
#Stream<[enum: 0..2, funs: [#Function<49.131689479/1 in Stream.map/2>]]>
6
```

As you can see it produced the same result but we didn't see the intermediate list,
instead we got a stream. It would be nice if we could inspect not the stream itself, but
each item produced. For that we'll use Stream.map to apply IO.inspect to each element.

```iex
iex(18)> Stream.map(0..2, &(&1*2)) |> Stream.map(&IO.inspect/1) |> Enum.sum()
0
2
4
6
```

And voila. I know it's a very simple example but hopefully it gave you a feel for how you
can use Streams to process data.

Erlang Solutions have a really good article about [using Streams for efficiency
gains](https://www.erlang-solutions.com/blog/building-an-elixir-stream.html), I recommend
you check it out.

## Define modules in the shell

This might not be a huge deal, but for me it's great that I can use the shell to quickly
test out anything I'm uncertain about. See an example of this in the next section.

## Use

Maybe it's because of my Python background, but sometimes I found myself yearning for
something like inheritance to reduce boilerplate in my Erlang code. So I'm very happy to
see Elixir's
[use](https://elixir-lang.org/getting-started/alias-require-and-import.html#use).
Now, while it might look like inheritance at first glance, it's actually macro expansion.

Here's an example:

```iex
iex(1)> defmodule MyServer do
...(1)>   use GenServer
...(1)>   def init(:ok) do
...(1)>     {:ok, %{}}
...(1)>   end
...(1)> end
{:module, MyServer,
 <<70, 79, 82, 49, 0, 0, 15, 32, 66, 69, 65, 77, 65, 116, 85, 56, 0, 0, 1, 152,
   0, 0, 0, 41, 15, 69, 108, 105, 120, 105, 114, 46, 77, 121, 83, 101, 114, 118,
   101, 114, 8, 95, 95, 105, 110, 102, 111, ...>>, {:init, 1}}
iex(2)> {:ok, pid} = GenServer.start_link(MyServer, :ok)
{:ok, #PID<0.119.0>}
```

# The stuff I'm not sure about

## Rebinding variables

In Elixir, unlike in Erlang, you can rebind variables. If you've programmed Erlang before,
the following code might look odd.

```iex
iex(5)> {a, b} = {1, 2}
{1, 2}

iex(6)> {a, b}
{1, 2}

iex(7)> {a, b} = {2, 2}
{2, 2}

iex(8)> a
2
```

Pattern matching is much like in Erlang. For example, this can't match because a would be
bound to two distinct values:

```iex
iex(1)> {a, a} = {1, 2}
** (MatchError) no match of right hand side value: {1, 2}
```

This is OK.

```iex
iex(1)> {a, a} = {2, 2}
```

To avoid rebinding a variable you must use the pin operator `^`.

This attempts to match a and leaves b to be (re)bound.

```iex
iex(1)> {^a, b} = {1, 2}
```

Also, just like Erlang, anything on the right hand side will never be bound, only
matched. So the following will never bind a or b, instead it will attempt a match:

```iex
iex(1)> {1, 2} = {a, b}
```

The downside for Erlang's match-unless-bound is you need to know which variables are
already bound. Elixir's pin operator is more explicit.

## Lower case variables, atoms and aliases

Erlang's approach, where anything that starts with a lowercase letter is an atom, and
anything capitalized is a variable, is just another one of it's quirks. Maybe you saw some
Elixir code, noticed all those lowercase variables, `:` as a prefix for atoms, and assumed
capitalization doesn't matter in Elixir... nope, capitalization still matters in Elixir. If
you type a capitalized word, because of another feature called Aliasing, you get an atom.

Elixir atoms:

```iex
iex(1)> is_atom(:abc)
true

iex(2)> to_string(:abc)
"abc"

iex(3)> is_atom(Abc)
true

iex(4)> Abc
Abc

iex(5)> to_string(Abc)
"Elixir.Abc"
```

I'd file this as a superficial difference however it adds one small problem, variables can
now potentially shadow functions. So when you write `is_number(1)` are you calling
`Kernel.is_number/1` or are you calling an anonymous function bound to the variable
`is_number`? In order to avoid the ambiguity in Elixir you have to add a dot after the
variable name when calling anonymous functions. So if you have a local variable named
is_number bound to a fun and want to call it, you'd use `is_number.(1)`.

# Some early conclusions
The biggest upside is the large and growing community plus the ecosystem of open source
packages. If you've ever searched for an Erlang package to solve some problem and
encountered 2 or 3 repos, neither having any activity in the last 3 years, you'll really
appreciate this.

Now on to something that irks me. Maybe because I've had Python's *"There should be one--
and preferably only one --obvious way to do it."* drilled in to my head for a decade I
find myself squirming a bit when I see all these:

 * Conditionals? In addition to Erlang's `cond` and `if` we also have `unless`. No biggie.

 * Should I `require` this module? `import` it? `use` it? There is good documentation
   about the differences, but I can't shake the feeling there are too many options.

 * Aliases. Not a complicated concept, but there seem to be many different ways to create
   an alias, and some are not explicit.

Still, when I see Erlang gen_server boilerplate and compare it with a simple Elixir
GenServer, all is forgiven.

# Next on my reading list

 * [Protocols](https://elixir-lang.org/getting-started/protocols.html).
 * [Macros](https://elixir-lang.org/getting-started/meta/quote-and-unquote.html). They
   seem to be quite powerful in Elixir
 * [Plug](https://hexdocs.pm/plug/readme.html)? The official way to write composable web
   applications in Elixir.
 * Maybe learn what the elixir app does, and why we need to start it to [call Elixir from
   Erlang](https://joearms.github.io/published/2016-03-13-Calling-Elixir-From_Erlang.html).
