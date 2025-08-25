from models import User, db

def find_matches_for_user(user_id, limit=10):
    """Find best matches for a given user, considering skills + metadata filters."""
    me = db.session.get(User, user_id)
    if not me:
        return []

    # My offers/wants
    my_wants = {us.skill for us in me.wanted}
    my_offers = {us.skill for us in me.offered}

    candidates = User.query.filter(User.id != me.id).all()
    scored = []

    for u in candidates:
        u_offers = {us.skill for us in u.offered}
        u_wants = {us.skill for us in u.wanted}

        score = 0

        # Complement: they offer what I want
        score += 3 * len({s.name.lower() for s in my_wants} & {s.name.lower() for s in u_offers})

        # Reciprocity: they want what I offer
        score += 2 * len({s.name.lower() for s in my_offers} & {s.name.lower() for s in u_wants})

        # Shared strengths
        score += 1 * len({s.name.lower() for s in my_offers} & {s.name.lower() for s in u_offers})

        # --- NEW filters / soft boosts ---
        # If location matches, give a slight boost
        my_locations = {s.location.lower() for s in my_offers | my_wants if getattr(s, "location", None)}
        u_locations = {s.location.lower() for s in u_offers | u_wants if getattr(s, "location", None)}
        if my_locations & u_locations:
            score += 1  # same area bonus

        # If category matches across any skill
        my_categories = {s.category.lower() for s in my_offers | my_wants if getattr(s, "category", None)}
        u_categories = {s.category.lower() for s in u_offers | u_wants if getattr(s, "category", None)}
        if my_categories & u_categories:
            score += 1  # similar field bonus

        # If difficulty levels align (e.g. both learning beginner-level skills)
        my_difficulties = {s.difficulty.lower() for s in my_offers | my_wants if getattr(s, "difficulty", None)}
        u_difficulties = {s.difficulty.lower() for s in u_offers | u_wants if getattr(s, "difficulty", None)}
        if my_difficulties & u_difficulties:
            score += 1

        if score:
            scored.append((score, u))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [u for _, u in scored[:limit]]
