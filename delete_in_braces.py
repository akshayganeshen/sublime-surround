#!/usr/bin/env python3

import sublime
import sublime_plugin


def get_left_character(view, region):
    ''' Returns the character immediately to the left of `region`. '''
    assert isinstance(view, sublime.View)
    assert isinstance(region, sublime.Region)
    start = region.begin()

    before_start = start - 1
    if before_start < 0:
        return ''

    return view.substr(before_start)


def get_right_character(view, region):
    ''' Returns the character immediately to the right of `region`. '''
    assert isinstance(view, sublime.View)
    assert isinstance(region, sublime.Region)
    end = region.end()

    after_end = end + 1 if region.empty() else end
    if after_end > len(view):
        return ''

    return view.substr(after_end)


def is_matching_braces(left_character, right_character):
    '''
    Returns `True` if `left_character` opens a brace that `right_character`
    is meant to close, and `False` otherwise.
    '''
    if left_character == '{' and right_character == '}':
        return True

    if left_character == '[' and right_character == ']':
        return True

    if left_character == '(' and right_character == ')':
        return True

    return False


def extract_whitespace_region(view):
    '''
    Returns a `sublime.Region` extended from a single, empty `selection` to
    include all whitespace characters.
    If the `selection` has multiple regions, or if the single region is
    non-empty, this will return `None`.
    If the extended region does not contain only whitespace, this will also
    return `None`.
    '''
    assert isinstance(view, sublime.View)
    selection = view.sel()

    if len(selection) != 1:
        return None

    first_region = selection[0]
    if not first_region.empty():
        return None

    # class specification for expanding the region
    # it is expanded until it reaches one of the following
    boundary_class = (
        sublime.CLASS_WORD_START | sublime.CLASS_WORD_END |
        sublime.CLASS_PUNCTUATION_START | sublime.CLASS_PUNCTUATION_END
    )
    whitespace_region = view.expand_by_class(
        first_region,
        boundary_class,
    )

    whitespace_buffer = view.substr(whitespace_region)
    if not whitespace_buffer.isspace():
        return None

    # seems legit!
    return whitespace_region


def is_region_in_braces(view, region):
    '''
    Returns `True` if `region` is contained within matching open and close
    braces on the left and right, respectively.
    '''
    left_character = get_left_character(view, region)
    right_character = get_right_character(view, region)

    return is_matching_braces(left_character, right_character)


class DeleteInBracesContext(sublime_plugin.EventListener):
    '''
    Context helper class.
    Provides a contextual trigger to specify when the text command should run.
    '''

    def on_query_context(self, view, key, operator, operand, match_all):
        if key != 'in_empty_braces':
            # not part of this plugin, so don't handle it
            return None

        if operator != sublime.OP_EQUAL and operator != sublime.OP_NOT_EQUAL:
            # can only do true/false, not sure how to do anything else
            return None

        if operand != True and operand != False:
            # can only compare to true/false, so don't handle it
            return None

        compare_as_true = (
            (operator == sublime.OP_EQUAL and operand == True) or
            (operator == sublime.OP_NOT_EQUAL and operand == False)
        )
        if compare_as_true:
            def compare_to_expected(is_applicable):
                return is_applicable
        else:
            def compare_to_expected(is_applicable):
                return not is_applicable

        whitespace_region = extract_whitespace_region(view)
        
        if not whitespace_region:
            # no region, so definitely not applicable
            return compare_to_expected(False)

        in_braces = is_region_in_braces(view, whitespace_region)
        return compare_to_expected(in_braces)


class DeleteInBraces(sublime_plugin.TextCommand):

    def run(self, edit):
        if not self.is_enabled():
            return

        view = self.view
        whitespace_region = extract_whitespace_region(view)

        if not whitespace_region:
            # no region, so nothing to delete, abort
            return

        if is_region_in_braces(view, whitespace_region):
            view.erase(edit, whitespace_region)

    def is_enabled(self):
        view = self.view
        whitespace_region = extract_whitespace_region(view)
        if not whitespace_region:
            return False
        return is_region_in_braces(view, whitespace_region)

    def is_visible(self):
        return False

    def description(self):
        return 'delete in braces'
