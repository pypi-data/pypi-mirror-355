# Java-Python-Adapter (Japy)

## What is Japy?

Japy is a library that allows calling Python methods from a Java process.

This can be useful, especially when you need some functionality that is much easier to implement in Python than in Java.

## How to use

Using Japy is no big deal. The only thing that you have to do is:

1. Decorate Python functions with `@japy_function`
2. Start a Japy server
3. Call functions from Java

A more detailed description is the following:

### Decorating Python function

Japy automatically scans Python files to detect functions which should be callable from a Java Process. For this, it is
necessary that these functions are decorated with `@japy_function`.

The following example shows what to do:

````python
# File: math_functions.py

from japy.japy_function import japy_function


# This function is callable from Java
@japy_function
def add(a, b):
    return a + b


# This function is not callable from Java
def subtract(a, b):
    return a - b
````

As you can see in the example, if a function is not decorated with `@japy_function` it is simply not callable from Java.

### Creating a File Scanner

The second step is creating a File Scanner. This can be done by the method `from_relative_path`.

````python
# File: my_japy_server.py

from japy.japy_file_scanner import from_relative_path

file_scanner = from_relative_path(".")
````

Assuming the path of the `my_japy_server.py` is `/home/python/src/japy/my_japy_server.py`. Then multiple calls
of `from_relative_path` are possible:

| Method-Call                   | Scanner entrypoint is         |
|-------------------------------|-------------------------------|
| from_relative_path(".")       | `/home/python/src/japy/`      |
| from_relative_path("..")      | `/home/python/src/`           |
| from_relative_path("../main") | `/home/python/src/main/`      |
| from_relative_path("/main")   | `/home/python/src/japy/main/` |

So the scanner takes a relative path, combines it with the current location of the caller script and scans everything
that is under the entrypoint path.

### Creating and Starting a Japy Server

When you have created a `JapyFileScanner` you are ready to get the server started.

For this, just do the following:

````python
# File: my_japy_server.py

from japy.japy_file_scanner import from_relative_path

file_scanner = from_relative_path(".")  # File Scanner from above

from japy.japy_server import get_japy_server_manager

server_manager = get_japy_server_manager(file_scanner)  # Get a JapyServerManager
server_manager.start_japy_server()  # Start the server
````

Now the server starts and searches for an available port.

Now, we can go ahead to the Java-Side.

### Using Japy in Java

First, include this library with Maven or Gradle into your project:

````xml

<dependency>
    <groupId>com.becker-freelance.japy</groupId>
    <artifactId>japy-adapter-java</artifactId>
    <version>1.0</version>
</dependency>
````

````groovy
dependencies {
    implementation 'com.becker-freelance.japy:japy-adapter-java:1.0'
}
````

Then you can create an `JapyPort`:

````java
import com.freelance.becker.japy.api.JapyPort;

JapyPort japyPort = JapyPort.getDefault();
````

With this, you can call Python Methods.

````java


import com.freelance.becker.japy.api.MethodReturnValue;
import com.freelance.becker.japy.api.PythonMethod;
import com.freelance.becker.japy.api.PythonMethodArgument;

import java.util.List;
import java.util.Optional;

PythonMethod method = new PythonMethod("add", List.of(
        new PythonMethodArgument<>(12),
        new PythonMethodArgument<>(31)
));

Optional<MethodReturnValue> returnValue = japyPort.callMethod(method);
````

If there are optional Arguments, these must not be provided to the list. Similar, if it is a `void` function, the List
with `PythonMethodArgument`s can be omitted.

The `MethodReturnValue` contains two fields:

1. `className`: The class name of the return value (Python names)
2. `returnValue`: The actual returned Value

If the return value in Python is a primitive datatype (`string`, `int`, `double`, `boolean`, `null`) the `returnValue`
contains the value directly.

If the return value in Python is not a primitive datatype, the `returnValue` contains a Map with its attributes. Then
you can use multiple variants to get your expected value:

1. `castExactly(Class<T>): T`: Transforms the return value into an Object of the given class. Attributes in this class
   which are not in return value are ignored and initialized with `null`
2. `castListWithSameClassesExactly(Class<T>): List<T>`: If the return value is a List wich contains elements of the same
   class, then this Method maps each object according to 1
3. `castListWithSameClassesExactly(Class<?>...): List<Object>`: If the List does contain more than one object, for each
   object in that List its type must be provided. Then each item in the List is mapped at its own according to 1
4. `mapCustom(MethodReturnValueMapper<T>): T`: You can also define a Mapper by yourself. This mapper accepts
   a `Map<String, Objects>` which represents an Object in JSON format


