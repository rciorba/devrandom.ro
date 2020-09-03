---
tags: elixir
title: Roll your own parameterized tests
published: 31st of December, 2020
tagline: >
  Or: How I learned to stop worrying and love Elixir Macros

---

# Unknowingly Reinventing the Wheel
TL;DR: I wrote my own "Parameterized Test" package because I didn't know about
https://github.com/KazuCocoa/ex_parameterized

# How this started: Parse nginx logs and write them to ES

I don't run any tracking on this site, because of privacy concerns. But I am curious if anyone ever
reads it, so I decided to load the logs into ElasticSearch, so I can look at them with Kibana.

But since I've done this before in Python, and I am trying to learn something else, let's implement
it in Elixir.

Because I didn't have the foresight to configure Nginx to log in a sane way, my logs are in the
default (Debian?) format, and I'll need to parse that. Of course I wrote a simple test based on one
of the actual logs, got that to work, aaaand it crashed on some other log line. So that became a
test as well. Rinse-repeat I ended up with this test covering 3 inputs:

```elixir
test "parse request" do
  assert Nginx.parse_request("GET /foo?bar=1&baz=2 HTTP/1.1") == {"GET", "/foo?bar=1&baz=2"}
  assert Nginx.parse_request("POST /%75%73%65%72%2e%70%68%70 HTTP/1.1") == {"POST", "/%75%73%65%72%2e%70%68%70"}
  assert Nginx.parse_request("\x03\x00\x00/*\xE0\x00\x00\x00\x00\x00Cookie: mstshash=Administr") == {nil, nil}
end
```

This is OK but if we're gonna be pedantic about it, it's not cool that this is just one test. What
if I change the parse_request function so that I break the second case? It won't even run the third
one.

# Parameterized tests considered awsesome

In the Python world there's a great testing framework called pytest. Pytest is great in many ways,
but if there's one feature I love the most, and the one I missed in ExUnit, that's parameterized
tests.

At it's core it's a simple thing. It generates multiple tests from a single definition and a list of
different inputs.

Incidentally Erlang's eunit has test generators, so parametrized tests are a natural fit. Amusingly
I assumed the lingo would be the same as Erlang's so I searched for "Elixir test generation", didn't
find anything useful, so I decided to learn about macros and implement this myself. It turns out
there's a hex package implementing what I wanted, but I only found out after I rolled my own.

# Macros and Abstract Syntax Trees

Macros are code which runs at compile time and generates code.

In the case of Elixir the macros need to generate Elixir AST nodes, not text (no nasty C
preprocessor biting your behind). Macros can also take arguments, and among those asguments you can
have ATS nodes. Let's define a simple macro, call it with a do block and inspect the arguments.

```iex
iex(1)> defmodule MyMacro do
...(1)>   defmacro macro(arg, do_block) do
...(1)>     IO.inspect(arg)
...(1)>     IO.inspect(do_block)
...(1)>   end
...(1)> end

iex(2)> require MyMacro  # make sure we can use the module's macros

ex(4)> MyMacro.macro(an_arg) do
...(4)>   IO.puts("i am now running")
...(4)>   a = 1
...(4)> end
{:an_arg, [line: 4], nil}  # the first argument. This is an AST node referencing a variable.
# the second argument is the do block. Notice it's a list of tuples:
[
  do: {:__block__, [],
   [
     {{:., [line: 5], [{:__aliases__, [line: 5], [:IO]}, :puts]}, [line: 5],
      ["i am now running"]},
     {:=, [line: 6], [{:a, [line: 6], nil}, 1]}
   ]}
]
```

# Doing it wrong? (Probably, but it's so lispy)

What's nice about the AST: it's just data! And we know how to manipulate data.

Reading about Elixir's macros I got the impression dealing with the AST is not how you're meant to
think about it, but personally it just makes most intuitive sense to me, especially given how close
to the code the AST is (almost a straight 1-to-1 mapping).


