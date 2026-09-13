"""Pace both authored fighters without changing the Spectrum position track.

Original eight-tick action cues are shorter than a complete modern animation.
Finish each accepted attack and recovery before sampling the current cue again;
Only a priority sweep cue is retained until recovery; ordinary conflicting
cues are coalesced instead of squeezing a whole animation into eight ticks.
"""


def complete_pose_track(fight_steps, select_attack, guard, bank_offset=0,
                        ticks_per_pose=4, priority_attack=None):
    """Schedule complete clips at one shared cadence in choreography ticks.

    The caller controls conversion from choreography ticks to PAL frames.
    Conflicting short cues are coalesced; positions are never modified here.
    """
    if ticks_per_pose < 1 or not fight_steps or not guard:
        raise ValueError('positive pose hold, script and guard required')
    track = []
    active = []
    elapsed = 0
    total = len(fight_steps) * 8
    pending = []
    previous_priority = []
    for tick in range(total):
        step = fight_steps[tick // 8]
        priority = priority_attack(step) if priority_attack else []
        if priority and priority != previous_priority:
            pending = priority
        previous_priority = priority
        if elapsed >= len(active) * ticks_per_pose:
            active = []
            elapsed = 0
            candidate = pending or select_attack(step)
            pending = []
            # Leave one guard hold at the seam; never chop a final attack.
            if candidate and tick + (len(candidate) + 1) * ticks_per_pose <= total:
                active = candidate
        if active:
            pose = active[elapsed // ticks_per_pose]
            elapsed += 1
        else:
            pose = guard[(tick // ticks_per_pose) % len(guard)]
        track.append(bank_offset + pose)
    return track


def jones_pose_track(fight_steps, selection, bank_offset=0, ticks_per_pose=4):
    """Use Jones's selection JSON and the common complete-clip scheduler."""
    lookup = {source: index for index, source in enumerate(selection['indices'])}
    groups = {}
    for name, (first, last) in selection['groups'].items():
        groups[name] = [lookup[source] for source in range(first, last + 1)]
    actions = {1: 'punch', 2: 'kick', 3: 'turning_kick',
               4: 'kick', 5: 'turning_kick'}
    # Avoid the unrelated profile-walk turn at movement edges.
    return complete_pose_track(
        fight_steps,
        lambda step: groups[actions[step[3]]] if step[3] else [],
        groups['guard'][:4], bank_offset, ticks_per_pose)


def mustermann_pose_track(fight_steps, source_indices, bank_offset=0,
                         ticks_per_pose=4):
    """Keep original source poses, split the three separate kick recoveries.

    Source frames 140..163 contains several kicks, not one 24-pose attack. Each selected
    subclip includes its wind-up, extension and recovery; no stride sampling.
    """
    lookup = {source: index for index, source in enumerate(source_indices)}
    def frames(first, last):
        return [lookup[source] for source in range(first, last + 1)]
    groups = {1: frames(17, 26), 2: frames(140, 148),
              3: frames(810, 818), 4: frames(148, 155),
              5: frames(155, 163)}
    def select(step):
        action = step[1]
        if action == 1 and step[3] == 4:
            return groups[3]  # Retain the duck/sweep response to a high kick.
        return groups[action] if action else []
    return complete_pose_track(fight_steps, select, frames(4, 7),
                               bank_offset, ticks_per_pose,
                               priority_attack=lambda step: groups[3]
                               if step[1] == 1 and step[3] == 4 else [])


def self_test():
    selection = {'indices': list(range(47)), 'groups': {
        'guard': [0, 7], 'punch': [8, 15], 'travel': [16, 23],
        'kick': [24, 33], 'turning_kick': [34, 46]}}
    # A one-step punch followed by conflicting kicks must finish, not jump.
    steps = [(0, 0, 0, 0), (0, 0, 0, 1), (0, 0, 0, 2)]
    steps += [(0, 0, 0, 0)] * 13
    track = jones_pose_track(steps, selection, bank_offset=56)
    assert len(track) == 128
    assert track[8:40] == [56 + pose for pose in range(8, 16) for _ in range(4)]
    assert all(56 <= pose < 103 for pose in track)
    assert all(pose < 60 for pose in track[40:])
    # An attack at the very end cannot be partially emitted across the seam.
    steps[-1] = (0, 0, 0, 3)
    assert jones_pose_track(steps, selection)[-8:] == [2] * 4 + [3] * 4
    mustermann = list(range(4, 27)) + list(range(140, 164)) + list(range(810, 819))
    steps = [(0, 0, 0, 0), (0, 2, 0, 2)] + [(0, 0, 0, 0)] * 14
    left = mustermann_pose_track(steps, mustermann)
    right = jones_pose_track(steps, selection)
    expected = [mustermann.index(source) for source in range(140, 149)
                for _ in range(4)]
    assert left[8:44] == expected  # Complete first kick, not all three kicks.
    assert right[8:48] == [pose for pose in range(24, 34) for _ in range(4)]
    for track in (left, right):
        assert all(track[i:i + 4] == [track[i]] * 4
                   for i in range(0, len(track), 4))
    steps[1] = (0, 1, 0, 4)
    sweep = mustermann_pose_track(steps, mustermann)
    assert sweep[8:44] == [mustermann.index(source) for source in range(810, 819)
                           for _ in range(4)]
    # A brief sweep cue during a kick is retained until that kick recovers.
    steps = [(0, 0, 0, 0), (0, 2, 0, 2), (0, 1, 0, 4)]
    steps += [(0, 0, 0, 0)] * 13
    paced = mustermann_pose_track(steps, mustermann, ticks_per_pose=2)
    assert paced[8:26] == [mustermann.index(source) for source in range(140, 149)
                           for _ in range(2)]
    assert paced[26:44] == [mustermann.index(source) for source in range(810, 819)
                            for _ in range(2)]
    print('Both fighters: complete attacks, equal pose holds, sweep and seam passed')


if __name__ == '__main__':
    self_test()
