package com.test.checkstyle;

public class Foo {
    private Foo(final Builder builder) {
        this.arg = builder.arg;
    }

    private final String arg;

    private static class Builder {
        private String arg;

        private void withArg(final String arg) {
            this.arg = arg;
        }

        private Foo build() {
            return new Foo(this);
        }
    }
}
