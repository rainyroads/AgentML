# AgentML
AgentML is in simple terms an XML dialect for creating natural language software agents. It is a project inspired by [AIML](http://www.alicebot.org/aiml.html) and [RiveScript](http://www.rivescript.com).

## Usage
To provide a quick example of how it works, here is a demonstration AML file that allows you to introduce yourself to an "agent"
```xml
<agentml version="0.2" xmlns="">
    <!-- Hello! -->
    <trigger>
        <pattern>(hello|hi|hiya|good evening|good morning)</pattern>

        <!-- Do we know this person already? -->
        <condition>
            <if name="first_name">
                <response priority="2">
                    <limit unit="minutes">3</limit>

                    <template>
                        <random>
                            <item>Hi <var name="first_name"/>!</item>
                            <item>Hello, <var name="first_name"/>!</item>
                            <item>Hello <var name="first_name"/>.</item>
                            <item><star format="capitalize"/> <var name="first_name"/>.</item>
                        </random>
                    </template>
                </response>

                <!-- We just said hello to them! -->
                <template priority="1">Hello yet again, <var name="first_name"/>.</template>
            </if>
        </condition>

        <!-- If not, let's ask them their name! -->
        <response>
            <topic>whats your name</topic>

            <template>
                <random>
                    <item>Hi! What is your name?</item>
                    <item>Hello! What's your name?</item>
                    <item>Hiya! Who are you?</item>
                    <item><star format="capitalize"/>! Who is this?</item>
                </random>
            </template>
        </response>
    </trigger>

    <!-- Response to us asking them their name -->
    <topic name="whats your name">
        <!-- First name only -->
        <trigger>
            <pattern>[my|the] [name is] (_)</pattern>

            <response>
                <var name="first_name"><star format="title"/></var>
                <topic/>

                <template>Hello, <star format="title"/>, it's nice to meet you!</template>
            </response>
        </trigger>

        <!-- First and last name (optional) -->
        <trigger priority="1">
            <pattern>[my|the] [name is] (_) (_)</pattern>

            <response>
                <var name="last_name"><star index="2" format="title"/></var>
                <redirect>my name is <star/></redirect>
            </response>
        </trigger>
    </topic>
</agentml>
```
Here is the above markup in action,
```
[#] Hello!
Hello! Who is this?

[#] My name is Makoto Fujimoto.
Hello, Makoto, it's nice to meet you!

[#] Hi!
Hello Makoto.

[#] Hello!
Hello yet again, Makoto.
```
In our first message, we introduce ourselves to the software agent. AgentML recognized that it doesn't know who we are yet and asks us our name, then saves our response data for use later. When we say hello again, the software agent greets us normally.

You can additionally see that if we repeat ourselves, the software agent can recognize that we are being a bit spammy and greets us in a slightly more annoyed tone. This is done by placing a limit on the response, and is one of the several features AgentML provides to allow you to create more in-depth, interactive software agents and chat bots.
 
As AgentML is currently still alpha software and functionality may change at any given time, there is no full documentation for using it available. However, you can review the current [Working Draft](https://github.com/FujiMakoto/AgentML/wiki/AgentML-0.2-Working-Draft) for a more technical overview of the software. 
 
## License
```
The MIT License (MIT)

Copyright (c) 2015 Makoto Fujimoto

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

## Help support AgentML's development!
If you'd like to help further AgentML's development, please consider pledging your support on Patreon!
https://www.patreon.com/FujiMakoto