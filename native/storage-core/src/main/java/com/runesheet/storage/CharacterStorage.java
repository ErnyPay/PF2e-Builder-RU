package com.runesheet.storage;

import java.util.List;

/**
 * RuneSheet-owned local character storage boundary.
 *
 * <p>The contract deliberately knows nothing about PF2e rules, Android UI,
 * cloud services, or a concrete database. Product clients may provide their own
 * character model while storage implementations own persistence and migration.</p>
 */
public interface CharacterStorage<T> {
    List<T> all();

    T create(T draft);

    void update(T item);

    void importCharacter(T item);

    void delete(String id);
}
