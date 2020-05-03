package com.test.checkstyle;

// This is a very long line which exceeds 140 chars and it's not a good practice to write such long lines because I cannot see a damn thing with my little screen.
public class Test {
    public final static String STATIC_FIELD = "static field";

    private final String arg;

    public Test(final String arg) {
        this.arg = arg;
    }

    public String getArg() {
        return this.arg;
    }
}
