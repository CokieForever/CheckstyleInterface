package com.test.checkstyle;

final class Bar {
    public static final String staticField = "static field";

    private Bar() {
    }

    static String concat(final String arg1, final String arg2) {
        return arg1 + arg2;
    }

    static int add(final int arg1, final int arg2) {
        return arg1 + arg2;
    }
}
