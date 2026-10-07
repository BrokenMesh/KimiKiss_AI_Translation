# Offline script interpreter (`scfvm`) and the Japanese regression test

`tools/qa/scfvm.py` runs the real bytecode of SCF classes offline, so a bytecode patch can be checked without the emulator. `tools/qa/test_patches_jp.py` uses it to prove that patches leave Japanese text unchanged. `tools/qa/test_scfvm.py` tests the interpreter itself. None of them contains game data: they read a directory of unpacked classes (`build/work/script_orig`, from `SCRIPT.IMG`) and, if present, the gitignored `text/*.json`.

```
python3 tools/qa/test_scfvm.py build/work/script_orig        # interpreter self-test + lint of all 5075 methods
python3 tools/qa/test_patches_jp.py build/work/script_orig   # every patches/scripts/*.asm, ~45 s
python3 tools/qa/test_patches_jp.py build/work/script_orig --only TextLine -v
```

`<script_dir>` must hold the **clean** classes: the test applies the patches to a temp copy itself and reports "input not clean" if a method is already patched.

## What it models

- **Loading.** A directory of `.scf` members, parsed with `tools/extract/scf.py`, classes loaded on demand. Superclass chain, instance variables (`fields`, the id is the slot), class variables (`fields2`, slot per class, shared), `methods` (instance side) and `methods2` (class side), constants (text as lists of codes, ints, float32, symbols, class references, nested arrays).
- **Every opcode of `docs/formats/scf.md`**: stack and temps (`push_nils` allocates locals), instance and class variables, all binary and unary operators, jumps, `and`/`or`/`not`, identity, sends and super sends (the search for a super send starts above the class that *defines* the running method), `at`/`at_put`, `try`/`throw`/`push_exception`/`clear_exception`, `primitive`. A throw cuts the stack back to the `try` depth and jumps to the handler; with no handler in the frame it unwinds into the caller. Strict where the real VM would corrupt memory: a temp, instance variable or jump target that does not exist raises `VMError`.
- **Real script classes run as bytecode**: `Vector`, `MyQueue`, `StringStream`, `Throwable` and the exception classes, `TextWindow`, `LogLine`, `TextLine*`, `ConfirmDialog`, `StaffRoll`, ... A real `TextWindow new`, `LogLine new:` or `StaffRoll new run` works.
- **Native (Python)**: `nil`, booleans, `Integer`/`Float` (`toFloat`, `toInteger`, `asChar`), `String` (`length`, `[]`, `put`, `+`, `=`, ...), `Array` (`new:`, `[]`, `atPut`, `copyFrom`, `equals`, ...), `Class` (`new` with 0–8 arguments, `name`, `findClass`), `Object` reflection (`getClass`, `isKindOf`, `perform*`, `sleep`).
- **Stubs** (`DEFAULT_STUBS`: `FontChar`, `FontCharEx`, `Sprite`, `DialogBox`, `Sound`, `ButtonGuide`, `Thread`, `System`, `ControlPad`, `WadaiParam`, `WadaiIcon`, `WadaiCursor`): their bytecode never runs. `new` and every other send, class side or instance side, is appended to `vm.log` as `Call(class, selector, args)` (`.recv` is the serial of the stub instance) and answered with `vm.stub_default` (the receiver itself) unless `vm.stub_results[(class, selector)]` (a value or `fn(vm, recv, args)`) says otherwise. Unknown selectors never crash. Add more with `VM(dir, stubs=DEFAULT_STUBS | {'GameParam'})` or `vm.stubs.add(...)`. Arguments are logged as snapshots (a `String` is copied, an object becomes `Ref(class name)`). `vm.live_log()` drops everything that involves a stub instance that was destroyed.
- **Lint** (`scfvm.lint_method`): static checks of one method: opcodes defined, jump targets on instruction starts, wide-send operand alignment (even offset), constant/instance variable/class variable/temp indices exist, operand stack depth the same on every path and never negative. All 5075 original methods pass, which also validates the stack effect of every opcode. `test_patches_jp.py` lints every patched method, tested or not.
- **Step limit**: `step_limit` opcodes per top-level `vm.send` (default 5,000,000) raises `StepLimitExceeded`; call depth is capped at 150.

## Assumptions (not confirmed against the ELF)

1. Integers are Python ints wrapped to 32 bits. The small-integer/boxed distinction is ignored. `/` and `%` truncate toward zero. Division by zero throws `DivisionByZeroException`. `&`, `|`, `^` on a float throw `IllegalArgument` (guess).
2. int op float and float op float give a float. Floats are rounded to float32 after every operation (round to nearest; the EE FPU truncates, which can differ in the last bit). The tests allow 1e-3.
3. `=` and `<>` compare numbers by value. For other receivers they are sent (`Object >> =` is identity; for `String` it is content equality, assumed). `==` is identity: ints by value, floats by value among floats, an int is never identical to a float.
4. Only `nil` and `false` are false; `0` is true. `and`/`or` pop two **already evaluated** operands: there is no short circuit. (Evidence: the stack-depth lint holds for the whole game with that effect.) A patch that writes `x ~~ nil and (x isKindOf: C)` therefore still sends `isKindOf:` to `nil`, which throws `DoesNotUnderstand` (`Nil >> isKindOf:` is a script method that throws).
5. `at`/`at_put` on an `Array` or `String` index directly (out of range throws `ArrayIndexOutOfBoundsException`); on any other receiver they send `[]` / `atPut` (that is how `Vector` works). `at_put` leaves the stored value on the stack.
6. `Class new` with N arguments allocates the object and runs `initialize` with N arguments; no matching `initialize` and N > 0 throws `DoesNotUnderstand`. `Array new: n` gives n nils, `String new` an empty string. `Integer asChar` gives a one-character string holding the code.
7. Text constants are shared mutable `String`s (as in the engine). Constant types 0/2/4 are read as nil/false/true (no game code pushes them).
8. A `34 n` primitive reached in a class that is neither stubbed nor native is logged like a stub call and a warning is recorded (`vm.warnings`).
9. No time and no threads: `sleep` returns at once, `Thread` is a stub, nothing runs concurrently.

## Writing a scenario

A scenario is a `Case(key, label, run)`. `key` is `Class.method/argc` of the patched method (the header of the `.asm` file), `run(vm)` builds receivers, sends messages and returns a VM-independent result (numbers, lists). The harness runs it on a fresh VM for the original and the patched class set and compares the result and the stub call log. Register a function that returns `(japanese_cases, english_cases)`:

```python
@scenarios('Foo.bar/1')
def _foo_cases(data):                      # data.by_display('TextLine') etc. = real game strings, if text/ exists
    def run_for(codes):
        def run(vm):
            foo = vm.new('Foo', 10, 0.0, 0.0)           # Class new: with 3 args (runs initialize)
            # or: vm.new_object('Foo', posX=1.0)         # no initialize, instance variables by name
            # vm.set_classvar('Foo', 'curX', 0.0)        # class variables by name
            # vm.stub_results[('WadaiParam', 'getDeckName')] = lambda vm, r, a: vm.string(codes)
            vm.send(foo, 'bar', [VString(codes)])
            return [vm.get_ivar(foo, 'posX')]
        return run
    ja = [Case('Foo.bar/1', f'ja #{i}', run_for(ja_codes(t))) for i, t in enumerate(GENERIC_JA)]
    en = [Case('Foo.bar/1', 'en', run_for(en_codes('Hello')), lang='en',
               summary=lambda vm, r: f'posX {r[0]:g}')]    # printed, not asserted
    return ja, en
```

`Case` options: `tol` (float tolerance, default 1e-3; `0.5` for centred lines, D-015), `mode='state'` (compare the final state of every glyph instead of the call sequence, for patches that deliberately add redundant calls), `project=lambda vm: vm.live_log()`, `stubs={...}` (extra stub classes), `steps=` (step limit), `soft=True` (a mismatch is only a warning: use when the *original* behaves wrongly), `oracle=fn(result)` (for `; add:` patches, which have no original to compare with), `why=` (shown with `-v`). A scenario that fails on the original, or raises on the patched set, is a failure: a shared crash does not count as a match. Text helpers: `ja_codes(str)` (`{...}` stays ASCII control code), `en_codes(str)` (D-012 English codes), `scfvm.sjis_codes(bytes)`.

A patched method without a registered scenario is printed as `UNTESTED` (with the static lint result); the exit status is 0 only if nothing failed.

## Limits of the tool

It checks what the stub calls and the instance state show, not pixels: a wrong glyph advance shows as a different `FontChar new` position, a wrong texture row does not. English runs only print a summary. Behaviour that depends on native code (`Sprite`, `DialogBox` layout, `GlyphCache`) is out of reach. The name-entry patches change Japanese behaviour on purpose (D-016) and need scenarios written against their specification, not Japanese identity.
