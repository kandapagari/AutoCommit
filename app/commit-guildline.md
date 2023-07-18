# Commit Guideline

These patterns are derived from several common guidelines, primarily from [￼Karma - Git Commit Msg  ￼Karma - Spectacular Test Runner for Javascript ], where we also got the following pattern from.

## Example

```
feat(gui): added language selection ability

Multi-language support is needed for cooperation with lower bavarians.
Now it's possible to let the use choose some preferred language via
drop-down menu.

Language-dependent terms are now set in centralized file i18n_gui.vars
as variables. However, English is still the only option until now.

```

## Pattern

A commit message should look like (blank lines should stay blank):

```
<''type''>(<''scope''>): <''subject''>

<''body''>

<''footer''>
```

### type

The type shall always be lower-case.

`build`: changes in build chain
`ci`: changes in CI chain, e.g. Jenkinsfile
`docs`: changes to the documentation may it be external (some html-files) or internal (doxygen)
`feat`: new, removed or changed feature for the user; not a new feature for build script (that would be of type chore)
`fix`: bugfix for the user; bug fix in build script may better typed with chore
`pref`: performance improvements
`refactor`: refactoring/restructuring production code; preserving (external) behaviour, though API may change; e.g. renaming a variable of function or merging two functions into one
`revert`: reverted commit or parts of it
`style`: code cosmetica like formatting, missing semi colons etc; no production code change
`test`: adding missing tests; refactoring tests; no production code change
`chore`: updating grunt tasks/maintaining etc; no production code change; e.g. new release/tag, edited list of contributors

### subject

The headline of the change

### scope

- The "scope" shall always be lower-case
- It can be empty (e.g. if the change is a global or difficult to assign to a single component), in which case the parentheses are omitted

### body

- optional; but if used, it must be preceded by a blank line.
- (longer) text that describes your commit; normally consists of multiple lines
- includes motivation/reason for the change and contrasts with previous behavior; explain ''what'' and ''why''
- may contain simple markdown code
- may contain blank lines

### footer

- optional; but if used, it must be preceded by a blank line.
- referencing issues (e.g. closes #234 or fixes #234)
- breaking changes (e.g. command line option for output has changed from '-o' to '--output') should be emphasized by preceding BREAKING CHANGE:.

#### length of lines

According to most of the guidelines including the git manual, the first line should be limited to 50 characters. However, in the log view GitHub cuts first line after 72 characters and replaces the remainder by ellipses (...).

Furthermore the lines of the body should not be longer than 72 characters according to most of the manuals.

This rule sometimes is called 50/72 rule. Some tools (such as vim) follow this rule by default. Karma actually uses a 70/80 rule; nevertheless if you use 50/72, you're still compatible to karma, but not v.v.

## FAQ

What (and why there) is the difference between refactor and style?
Usually the style changes (such as code indentation, line trimming, blank line insertion/deletion etc.) are not interesting to any developer; so most of them don't want/have to look at those changes (except for the poor code review guy).

But every developer should have a look at all refactor changes. These changes must not change the software behavior for the user. But the interior might have changed vastly.

There you have the distinction along with its motivation.

### Of which type is the addition of a new feature or bug-fix of the build script?

chore

### How shall we distinguish between an addition, deletion, deprecation or a change of a feature?￼

The "type" in all those cases is feat. The "subject" should contain information of the sub-type of the commit.

### May I use two or more types in one commit?￼

Even if your work can't be split in several commits, but contains parts of refactor and feature, then you should decide for ''one'' ''type'' only. If you implemented a new feature and needed to do some refactoring for that, then set the ''type'' as feat. If you just refactored the code and changed a feature by this, then use the ''type'' refactor
