import re
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from backend.app.schemas.analysis import (
    AnalyzeRequest,
    AnalyzeResponse,
    MessageAnalysis,
    MessageSignal,
    ParticipantInfo,
    TargetingInteraction,
    ConversationMetrics,
    ModelInfo,
    ContextInfo
)
from backend.app.services.parser import parse_conversation, ParsedMessage
from backend.app.services.nlp import classify_texts, classifier
from backend.app.services.features import (
    extract_all_features,
    infer_message_targets,
    ExtractedFeatures
)

class ContextGuardAnalysisEngine:
    """
    Modular Context-Aware Cyberbullying & Conversation Dynamics Engine.
    Combines conversational turn parsing, multi-turn dialogue context,
    sentiment-inversion sarcasm detection, relational metadata,
    and repeated-targeting asymmetry metrics.
    """

    def __init__(self):
        self.engine_name = "ContextGuard Hybrid Dialogue NLP Engine"
        self.version = "1.2.0"
        self.transformer_available = False
        self._init_transformer_pipeline()

    def _init_transformer_pipeline(self):
        # No local transformer is loaded. A package import is not model availability.
        self.transformer_available = False

    def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        return self.analyze_messages(parse_conversation(request.conversation), request.context)

    def analyze_messages(self, parsed_messages: List[ParsedMessage], context: Optional[ContextInfo] = None) -> AnalyzeResponse:
        """Analyze already structured messages without reparsing Unicode names or multiline text."""
        if not parsed_messages:
            return self._empty_response(context)

        features_list = extract_all_features(parsed_messages)
        statistical_results = classify_texts([message.text for message in parsed_messages])
        sender_target_pairs = infer_message_targets(parsed_messages)
        total_msgs = len(parsed_messages)

        context_info = context or ContextInfo()
        rel_lower = (context_info.relationship or "").lower()
        is_known_friendly = any(w in rel_lower for w in ["friend", "close", "gaming", "squad", "partner", "buddy"])
        is_high_risk_setting = any(w in rel_lower for w in ["stranger", "bully", "ex", "anonymous"]) or "public" in (context_info.setting or "").lower()

        # Step 1: Detect Global Conversation Dynamics
        # Check if conversation is dominated by reciprocal laughter/playfulness
        has_reciprocal_laughter = self._check_reciprocal_laughter(features_list, parsed_messages)
        speaker_target_hostile_counts = defaultdict(int)
        speaker_target_banter_counts = defaultdict(int)
        participant_sent = defaultdict(int)
        participant_harmful_sent = defaultdict(int)
        participant_targeted_count = defaultdict(int)
        participant_harm_targeted_count = defaultdict(int)

        analyzed_messages: List[MessageAnalysis] = []

        for idx, (msg, feat) in enumerate(zip(parsed_messages, features_list)):
            sender, target = sender_target_pairs[idx]
            participant_sent[sender] += 1
            if target:
                participant_targeted_count[target] += 1

            # Multi-turn conversational window inspection
            prev_feat = features_list[idx - 1] if idx > 0 else None
            prev_msg = parsed_messages[idx - 1] if idx > 0 else None
            next_feat = features_list[idx + 1] if idx + 1 < total_msgs else None
            next_msg = parsed_messages[idx + 1] if idx + 1 < total_msgs else None
            prior_features = features_list[:idx]
            prior_messages = parsed_messages[:idx]

            # Classification logic
            classification, conf_score, conf_cat, pattern, evidence, alt_interp, action, signals = self._classify_turn(
                idx=idx,
                total_msgs=total_msgs,
                msg=msg,
                feat=feat,
                sender=sender,
                target=target,
                prev_msg=prev_msg,
                prev_feat=prev_feat,
                next_msg=next_msg,
                next_feat=next_feat,
                prior_features=prior_features,
                prior_messages=prior_messages,
                has_reciprocal_laughter=has_reciprocal_laughter,
                is_known_friendly=is_known_friendly,
                is_high_risk_setting=is_high_risk_setting,
                context_info=context_info,
                speaker_target_hostile_counts=speaker_target_hostile_counts
            )

            if classification in ["Possible Cyberbullying", "Threat / Urgent Concern", "Potentially Harmful"]:
                if target:
                    speaker_target_hostile_counts[(sender, target)] += 1
                    participant_harm_targeted_count[target] += 1
                participant_harmful_sent[sender] += 1
            elif classification == "Friendly Banter":
                if target:
                    speaker_target_banter_counts[(sender, target)] += 1

            # Targeting pattern description for this message
            if target and speaker_target_hostile_counts[(sender, target)] > 1:
                targeting_desc = f"Repeated turn ({speaker_target_hostile_counts[(sender, target)]}x) directed from {sender} toward {target}."
            elif target:
                targeting_desc = f"Directed from {sender} toward {target}."
            else:
                targeting_desc = f"Broadcast turn by {sender}."

            analyzed_messages.append(
                MessageAnalysis(
                    id=msg.id,
                    speaker=msg.speaker,
                    target=target,
                    text=msg.text,
                    classification=classification,
                    confidence_score=round(conf_score, 2),
                    confidence_category=conf_cat,
                    detected_pattern=pattern,
                    contextual_evidence=evidence,
                    targeting_pattern=targeting_desc,
                    alternative_interpretation=alt_interp,
                    suggested_action=action,
                    signals=signals,
                    statistical_assessment=statistical_results[idx],
                )
            )

        # Step 2: Participant & Targeting Matrix
        participants_info: List[ParticipantInfo] = []
        all_participants = sorted(list(set(participant_sent.keys()) | set(participant_targeted_count.keys())))

        for p in all_participants:
            sent_total = participant_sent[p]
            harmful_total = participant_harmful_sent[p]
            targeted_harmful_total = participant_harm_targeted_count[p]

            if harmful_total >= 2:
                role = "Frequent source of hostile or exclusionary utterances"
            elif targeted_harmful_total >= 2 and harmful_total == 0:
                role = "Repeated recipient of hostile or exclusionary turns without retaliating"
            elif targeted_harmful_total == 1 and harmful_total == 0:
                role = "Target of an isolated negative or ambiguous turn"
            elif sent_total > 0 and harmful_total == 0:
                role = "Participant in neutral or reciprocal dialogue"
            else:
                role = "Intermittent participant"

            participants_info.append(
                ParticipantInfo(
                    name=p,
                    messages_sent=sent_total,
                    harmful_sent=harmful_total,
                    targeted_count=targeted_harmful_total,
                    role_summary=role
                )
            )

        targeting_interactions: List[TargetingInteraction] = []
        for (src, tgt), hostile_count in speaker_target_hostile_counts.items():
            banter_count = speaker_target_banter_counts.get((src, tgt), 0)
            reverse_hostile = speaker_target_hostile_counts.get((tgt, src), 0)
            is_asym = hostile_count > 0 and reverse_hostile == 0

            if is_asym and hostile_count >= 2:
                desc = f"Asymmetric hostile targeting: {src} repeatedly targets {tgt} ({hostile_count} turns) with no observed reciprocal aggression."
            elif is_asym:
                desc = f"Unreciprocated negative statement from {src} to {tgt}."
            else:
                desc = f"Bilateral or mixed conflict between {src} and {tgt}."

            targeting_interactions.append(
                TargetingInteraction(
                    source=src,
                    target=tgt,
                    harmful_turns=hostile_count,
                    banter_turns=banter_count,
                    description=desc,
                    is_asymmetric=is_asym
                )
            )

        # Step 3: Conversation-Level Risk & Metric Synthesis
        harmful_count = sum(1 for m in analyzed_messages if m.classification in ["Potentially Harmful", "Possible Cyberbullying", "Threat / Urgent Concern"])
        cyberbullying_count = sum(1 for m in analyzed_messages if m.classification == "Possible Cyberbullying")
        threat_count = sum(1 for m in analyzed_messages if m.classification == "Threat / Urgent Concern")
        uncertain_count = sum(1 for m in analyzed_messages if m.classification == "Uncertain — More Context Needed")
        banter_count = sum(1 for m in analyzed_messages if m.classification == "Friendly Banter")
        neutral_count = sum(1 for m in analyzed_messages if m.classification == "Harmless / Neutral")

        has_direct_lethal_threat = any(f.has_direct_threat for f in features_list)
        has_confrontation_threat = any(f.has_confrontation for f in features_list)
        has_retaliatory_escalation = any(f.has_retaliatory for f in features_list)
        has_boundary_fear = any(f.has_boundary_fear for f in features_list)
        has_bystander_defense = any(f.has_bystander_defense for f in features_list)
        has_stop_request = any(f.has_explicit_stop_request for f in features_list)

        overall_risk, estimated_risk_score, risk_summary, recommendations = self._synthesize_risk(
            total_msgs=total_msgs,
            harmful_count=harmful_count,
            cyberbullying_count=cyberbullying_count,
            threat_count=threat_count,
            uncertain_count=uncertain_count,
            banter_count=banter_count,
            targeting_interactions=targeting_interactions,
            is_known_friendly=is_known_friendly,
            has_direct_lethal_threat=has_direct_lethal_threat,
            has_confrontation_threat=has_confrontation_threat,
            has_retaliatory_escalation=has_retaliatory_escalation,
            has_boundary_fear=has_boundary_fear,
            has_bystander_defense=has_bystander_defense,
            has_stop_request=has_stop_request
        )

        metrics = ConversationMetrics(
            total_messages=total_msgs,
            potentially_harmful_count=harmful_count,
            uncertain_count=uncertain_count,
            friendly_banter_count=banter_count,
            neutral_count=neutral_count,
            threat_count=threat_count,
            participant_count=len(all_participants)
        )

        model_info = ModelInfo(
            engine_name="ContextGuard Local Contextual NLP Pipeline",
            engine_type="Context rules with a separately reported trained comment classifier" if classifier() is not None else "Multi-turn dialogue rules",
            execution_mode="Local analysis; hosted review requires a separate explicit request",
            description="Analyzes conversational history, turn-taking reciprocity, sarcasm markers, and targeting asymmetry.",
            transparency_notes="Conversation risk is rule-based. The trained classifier estimates standalone comment toxicity separately and does not override conversation risk. Neither score is statistically calibrated."
        )

        limitations = [
            "Decision-Support Only: This system estimates conversational risk patterns and cannot definitively determine human intent or psychological state.",
            "Cultural & Linguistic Variance: Sarcasm, regional slang, and in-group humor can lead to false positives or false negatives.",
            "Information Asymmetry: Real-world relationships, voice tone, facial expressions, and off-platform interactions are invisible to text analysis.",
            "Not for Disciplinary Automation: Never use this tool as the sole basis for sanctioning or disciplinary actions without human review."
        ]

        return AnalyzeResponse(
            conversation_summary=risk_summary,
            overall_risk=overall_risk,
            risk_score=estimated_risk_score,
            confidence="High" if total_msgs > 2 and threat_count == 0 and uncertain_count <= 1 else "Moderate / Context Dependent",
            metrics=metrics,
            messages=analyzed_messages,
            participants=participants_info,
            targeting_patterns=targeting_interactions,
            recommendations=recommendations,
            model_info=model_info,
            limitations=limitations
        )

    def _check_reciprocal_laughter(self, features: List[ExtractedFeatures], msgs: List[ParsedMessage]) -> bool:
        """Determines if multiple distinct speakers share laughter or playful banter emojis."""
        speakers_laughing = set()
        for f, m in zip(features, msgs):
            if f.has_laughter or f.has_playful_emoji:
                speakers_laughing.add(m.speaker)
        return len(speakers_laughing) >= 2

    def _classify_turn(
        self,
        idx: int,
        total_msgs: int,
        msg: ParsedMessage,
        feat: ExtractedFeatures,
        sender: str,
        target: Optional[str],
        prev_msg: Optional[ParsedMessage],
        prev_feat: Optional[ExtractedFeatures],
        next_msg: Optional[ParsedMessage],
        next_feat: Optional[ExtractedFeatures],
        prior_features: List[ExtractedFeatures],
        prior_messages: List[ParsedMessage],
        has_reciprocal_laughter: bool,
        is_known_friendly: bool,
        is_high_risk_setting: bool,
        context_info: ContextInfo,
        speaker_target_hostile_counts: Dict[Tuple[str, str], int]
    ) -> Tuple[str, float, str, str, List[str], Optional[str], str, MessageSignal]:
        """
        Classifies an individual turn by looking at its own features AND the surrounding multi-turn dialogue context.
        """
        evidence: List[str] = []
        signals = MessageSignal(
            has_laughter=feat.has_laughter,
            has_playful_emoji=feat.has_playful_emoji,
            has_exclusion_phrase=feat.has_exclusion,
            has_insult_lexicon=feat.has_insult,
            has_threat_lexicon=(feat.has_direct_threat or feat.has_confrontation),
            is_sarcasm_suspect=feat.has_sarcasm_praise,
            is_reciprocal_tease=False,
            is_repeated_target=False,
            is_victim_protest=(feat.has_protest or feat.has_boundary_fear),
            is_retaliatory_threat=feat.has_retaliatory,
            has_confrontation=feat.has_confrontation,
            has_intimidation=feat.has_ominous_warning
        )

        prior_hostile_count = 0
        if target:
            prior_hostile_count = speaker_target_hostile_counts.get((sender, target), 0)
        general_prior = sum(count for (s, t), count in speaker_target_hostile_counts.items() if s == sender)
        prior_hostile_count = max(prior_hostile_count, general_prior)
        signals.is_repeated_target = prior_hostile_count >= 1

        # ----------------------------------------------------
        # RULE 0: Friendly Banter & Reciprocal Teasing Override
        # (False Positive Prevention: playful friends teasing each other)
        # ----------------------------------------------------
        is_teasing_with_laughter = (feat.has_laughter or feat.has_playful_emoji) and (feat.has_sarcasm_praise or feat.has_insult or feat.has_retaliatory)
        has_subsequent_laughter = (next_feat and (next_feat.has_laughter or next_feat.has_playful_emoji or next_feat.has_sarcasm_praise))
        has_prior_laughter = (prev_feat and (prev_feat.has_laughter or prev_feat.has_playful_emoji))

        if not feat.has_direct_threat and not feat.has_confrontation:
            if is_teasing_with_laughter or (has_reciprocal_laughter and (feat.has_sarcasm_praise or feat.has_laughter or "rematch" in feat.text_lower or "nobel" in feat.text_lower)):
                signals.is_reciprocal_tease = True
                evidence.append("Playful banter cues present (laughter expressions, laughing emojis, or self-deprecating humor).")
                if has_subsequent_laughter or has_prior_laughter:
                    evidence.append("Mutual reciprocal participation: surrounding interlocutors responded with humor, playful escalation, or agreement.")
                if is_known_friendly:
                    evidence.append(f"Contextual prior: Participants are identified as '{context_info.relationship}'.")

                alt_interp = "If the recipient secretly feels uncomfortable, teasing could occasionally cross personal boundaries even if smiles/emojis are used."
                action = "No intervention needed. Conversation demonstrates healthy peer banter. Check in with participants only if someone expresses discomfort."

                return (
                    "Friendly Banter",
                    0.89,
                    "High",
                    "Reciprocal Playful Banter",
                    evidence,
                    alt_interp,
                    action,
                    signals
                )

        # ----------------------------------------------------
        # RULE 1: Direct Physical / Violent Threat (Severe Concern)
        # ----------------------------------------------------
        if feat.has_direct_threat:
            evidence.append("Explicit violent or lethal threat phrasing detected ('hurt', 'kill', 'punch', 'beat', etc.).")
            alt_interp = "Could theoretically be gaming hyperbole, but safety protocols require treating direct threats with urgency."
            action = "Immediately prioritize personal safety. Save conversation records and report to a trusted adult, educator, or platform administrator."
            return (
                "Threat / Urgent Concern",
                0.95,
                "High",
                "Direct Physical / Violent Threat",
                evidence,
                alt_interp,
                action,
                signals
            )

        # ----------------------------------------------------
        # RULE 2: Real-World In-Person Confrontation Threat
        # ----------------------------------------------------
        if feat.has_confrontation:
            evidence.append("Specifies concrete real-world location or timeframe for in-person confrontation ('find you after college tomorrow', 'outside', etc.).")
            had_prior_report = any(f.has_report_or_grievance for f in prior_features)
            had_prior_retaliatory = any(f.has_retaliatory for f in prior_features)

            if had_prior_retaliatory or had_prior_report:
                evidence.append("Escalates from preceding retaliatory statement following participant's reported abuse complaint.")
            if not feat.has_laughter and not feat.has_playful_emoji:
                evidence.append("Absence of playful markers, emojis, or reciprocal teasing supports genuine confrontation intent.")

            alt_interp = "Could represent rhetorical posturing, but naming a concrete future location and timeframe indicates serious potential for in-person confrontation."
            action = "Prioritize immediate physical safety. Avoid isolated areas around college or meeting locations, notify campus authorities, and preserve chat records."

            return (
                "Threat / Urgent Concern",
                0.91,
                "High",
                "Real-World / In-Person Confrontation Threat",
                evidence,
                alt_interp,
                action,
                signals
            )

        # ----------------------------------------------------
        # RULE 3: Reinforced Threat / Persistent Intimidation
        # ----------------------------------------------------
        if feat.has_ominous_warning:
            had_prior_threat = any(f.has_direct_threat or f.has_confrontation for f in prior_features)
            had_prior_retaliatory = any(f.has_retaliatory for f in prior_features)
            had_prior_boundary = any(f.has_boundary_fear for f in prior_features)

            if had_prior_threat or had_prior_retaliatory:
                evidence.append("Persistent intimidation reinforcing a prior confrontation threat or retaliatory warning.")
                if had_prior_boundary or (prev_feat and prev_feat.has_boundary_fear):
                    evidence.append("Directly disregards recipient's explicit boundary demand to stay away ('Don't come near me').")
                evidence.append("Maintains psychological pressure focusing on upcoming timeframe ('worried about tomorrow').")

                alt_interp = "Could represent verbal posturing, but persistence following explicit boundary assertion demonstrates intentional intimidation."
                action = "Treat persistent intimidation as an active safety concern. Alert college administration, security, or law enforcement."

                return (
                    "Threat / Urgent Concern",
                    0.88,
                    "High",
                    "Reinforced Threat / Persistent Intimidation",
                    evidence,
                    alt_interp,
                    action,
                    signals
                )
            else:
                evidence.append("Ominous warning phrasing ('should be worried') detected without prior dispute context.")
                alt_interp = "Could be dramatic exaggeration or non-physical warning; text alone is ambiguous."
                action = "Seek additional conversational context before inferring malicious intent."
                return (
                    "Potentially Harmful",
                    0.65,
                    "Moderate",
                    "Veiled Warning / Ambiguous Intimidation",
                    evidence,
                    alt_interp,
                    action,
                    signals
                )

        # ----------------------------------------------------
        # RULE 4: Retaliatory Intimidation / Consequence Warnings
        # ----------------------------------------------------
        if feat.has_retaliatory:
            had_prior_report = any(f.has_report_or_grievance for f in prior_features)
            had_prior_stop_request = any(f.has_explicit_stop_request for f in prior_features)
            had_prior_insult_pattern = prior_hostile_count >= 1
            if had_prior_report:
                evidence.append("Veiled retaliatory warning ('regret doing that') immediately following participant's assertion of reporting abusive behavior.")
                evidence.append("Contextual connection to prior complaint indicates possible payback or retribution.")
                alt_interp = "Could theoretically express intent to take administrative or platform counter-action, but in the context of abusive messaging reports, it conveys intimidation."
                action = "Document this statement as retaliatory posturing. Avoid 1-on-1 engagement and keep records for platform or institutional review."

                return (
                    "Potentially Harmful",
                    0.78,
                    "Moderate",
                    "Retaliatory Intimidation / Consequence Warning",
                    evidence,
                    alt_interp,
                    action,
                    signals
                )
            elif had_prior_stop_request and had_prior_insult_pattern:
                # Victim explicitly asked the sender to stop; sender responds with a threat
                evidence.append("Retaliatory consequence warning issued directly after the recipient explicitly asked the sender to stop ('please stop', 'I'm asking you to stop').")
                evidence.append(f"Follows {prior_hostile_count} prior hostile turn(s); the stop request was ignored and then weaponised.")
                alt_interp = "Could theoretically express non-violent frustration, but issuing a consequence warning after an explicit stop request demonstrates intentional intimidation."
                action = "Document this statement. The pattern of ignoring a stop request and then threatening warrants platform moderation or reporting."
                return (
                    "Potentially Harmful",
                    0.80,
                    "Moderate",
                    "Retaliatory Warning After Explicit Stop Request",
                    evidence,
                    alt_interp,
                    action,
                    signals
                )
            elif total_msgs <= 2:
                evidence.append("Isolated phrase ('regret that') without surrounding dialogue context or reported dispute.")
                alt_interp = "Could refer to game moves, professional decisions, or non-threatening colloquial regret."
                action = "Seek additional conversational context before inferring malicious intent."
                return (
                    "Uncertain — More Context Needed",
                    0.55,
                    "Low / Uncertain",
                    "Ambiguous Consequence Warning",
                    evidence,
                    alt_interp,
                    action,
                    signals
                )
            else:
                evidence.append("Warning of negative consequences ('you'll regret this') within an ongoing exchange.")
                alt_interp = "Could express severe disagreement or non-violent dispute resolution."
                action = "Monitor conversation to assess whether hostility escalates into threats."
                return (
                    "Potentially Harmful",
                    0.68,
                    "Moderate",
                    "Retaliatory Warning",
                    evidence,
                    alt_interp,
                    action,
                    signals
                )

        # ----------------------------------------------------
        # RULE 5: Recipient Boundary Assertion / Fear / Clarification Inquiry
        # ----------------------------------------------------
        if feat.has_boundary_fear:
            had_prior_threat = any(f.has_direct_threat or f.has_confrontation or f.has_retaliatory for f in prior_features)
            if had_prior_threat:
                evidence.append("Recipient explicitly orders the sender not to approach ('Don't come near me') and emphasizes seriousness ('I'm serious').")
                evidence.append("Demonstrates active objection, fear, or refusal of real-world contact following confrontation statements.")
                alt_interp = "Speaker is stating personal boundaries and distress, not initiating aggression."
                action = "Support the recipient's boundary and ensure physical distance is respected."
                return (
                    "Uncertain — More Context Needed",
                    0.76,
                    "Moderate",
                    "Explicit Boundary Assertion / Distress Indicator",
                    evidence,
                    alt_interp,
                    action,
                    signals
                )

        if feat.has_inquiry:
            had_prior_ominous = any(f.has_retaliatory or f.has_ominous_warning or f.has_sarcasm_praise for f in prior_features)
            # Also treat "What does that mean?" as victim distress if there were prior insults
            had_prior_hostile = prior_hostile_count >= 1
            if had_prior_ominous or had_prior_hostile:
                evidence.append("Recipient questions intent following an ominous retaliatory statement ('What does that mean?').")
                evidence.append("Indicates uncertainty or distress regarding the preceding veiled consequence warning.")
                alt_interp = "Standard clarification question indicating ambiguity or discomfort."
                action = "Clarify intent directly or step back from escalating conflict."
                return (
                    "Uncertain — More Context Needed",
                    0.70,
                    "Moderate",
                    "Clarification Inquiry / Ambiguity Response",
                    evidence,
                    alt_interp,
                    action,
                    signals
                )

        # ----------------------------------------------------
        # ----------------------------------------------------
        # RULE 5.5: Explicit Stop Request (Victim asking sender to cease harassment)
        # Catches polite but unambiguous pleas: "please stop", "I'm asking you to stop",
        # "I've asked you before to stop", "stop making personal comments"
        # ----------------------------------------------------
        if feat.has_explicit_stop_request:
            evidence.append("Speaker explicitly requests that the other person stop ('please stop', 'I've asked you before to stop', 'stop making personal comments').")
            evidence.append("This is an unambiguous victim boundary assertion and de-escalation attempt.")
            alt_interp = "Speaker is setting a verbal boundary; the request itself is not hostile."
            action = "Validate the speaker's request. If the other party continues, escalate to platform moderation."
            return (
                "Uncertain — More Context Needed",
                0.75,
                "Moderate",
                "Victim Explicit Stop Request",
                evidence,
                alt_interp,
                action,
                signals
            )

        # ----------------------------------------------------
        # RULE 6: Reporting / Grievance Explanations
        # ----------------------------------------------------
        if feat.has_report_or_grievance:
            if "why" in feat.text_lower:
                evidence.append("Inquiry regarding account reporting status without overt hostility.")
                pattern = "Account Inquiry / Grievance"
            else:
                evidence.append("Factual statement explaining the basis for reporting abusive messages or setting boundaries.")
                pattern = "Reporting Explanation / Boundary Assertion"
            alt_interp = "Routine accountability discussion regarding digital interaction standards."
            action = "Keep communication objective and rely on official platform reporting channels."
            return (
                "Harmless / Neutral",
                0.90,
                "High",
                pattern,
                evidence,
                alt_interp,
                action,
                signals
            )

        # ----------------------------------------------------
        # RULE 6.5: Bystander Defence / Supportive Intervention
        # A third-party participant is actively defending the target.
        # Must be checked BEFORE Rule 7 (Social Exclusion) to prevent
        # defence phrases like "just leave Sam alone" from triggering
        # the exclusion detector.
        # ----------------------------------------------------
        if feat.has_bystander_defense:
            had_prior_hostile_in_conv = any(f.has_insult or f.has_exclusion or f.has_covert_exclusion or f.has_retaliatory for f in prior_features)
            evidence.append("A bystander or third-party participant is actively intervening to defend another participant ('cut it out', 'that's unnecessary', 'leave them alone').")
            if had_prior_hostile_in_conv:
                evidence.append("Intervention occurs in the context of prior hostile or exclusionary turns; the bystander is standing up for a recipient of repeated targeting.")
            alt_interp = "The speaker is not initiating hostility; they are attempting to de-escalate a conflict."
            action = "Acknowledge and support the bystander's intervention. This is a prosocial behaviour."
            return (
                "Harmless / Neutral",
                0.90,
                "High",
                "Bystander Defence / Supportive Intervention",
                evidence,
                alt_interp,
                action,
                signals
            )

        # ----------------------------------------------------
        # RULE 7: Social Exclusion / Hostile Rejection (Overt & Covert)
        # ----------------------------------------------------
        if feat.has_exclusion or feat.has_covert_exclusion:
            signals.has_exclusion_phrase = True
            if feat.has_exclusion:
                evidence.append("Systemic exclusionary language detected ('nobody wants you', 'leave the group', 'stop talking', 'don't expect an invitation', etc.).")
            else:
                evidence.append("Indirect or covert exclusionary statement detected ('meetings go better when certain people aren't there', 'team works better without distractions', etc.).")

            if prior_hostile_count >= 1:
                evidence.append(f"Follows {prior_hostile_count} previous hostile or exclusionary turn(s) from {sender} toward {target or 'the participant'}.")
                classification = "Possible Cyberbullying"
                pattern = "Repeated Social Exclusion & Harassment"
                conf = 0.88 if feat.has_exclusion else 0.85
                action = "Recognize this as persistent exclusion. Consider stepping away from this group, seeking support, or archiving the conversation for moderation."
                alt_interp = "Unlikely to be friendly teasing given the lack of playful cues and repeated unreciprocated hostility."
            else:
                classification = "Possible Cyberbullying" if (feat.has_exclusion and not is_known_friendly) else "Potentially Harmful"
                pattern = "Social Exclusion & Ostracism" if feat.has_exclusion else "Indirect / Covert Social Exclusion"
                conf = 0.81 if feat.has_exclusion else 0.76
                action = "Set clear boundaries or ask a moderator or team lead to intervene if this behavior continues."
                alt_interp = "Could represent an emotional venting moment during an argument rather than systematic cyberbullying."

            return (
                classification,
                conf,
                "High" if conf > 0.85 else "Moderate",
                pattern,
                evidence,
                alt_interp,
                action,
                signals
            )

        # ----------------------------------------------------
        # RULE 7.2: Dismissive Invalidation / Gaslighting
        # Aggressor dismisses victim's boundary request ("I'm not making personal comments, just telling the truth")
        # ----------------------------------------------------
        if feat.has_dismissive and not feat.has_laughter:
            had_prior_stop = any(f.has_explicit_stop_request for f in prior_features)
            had_prior_protest = any(f.has_protest for f in prior_features)
            if had_prior_stop or had_prior_protest or prior_hostile_count >= 1:
                evidence.append("Speaker invalidates or dismisses the recipient's boundary request ('just telling the truth', 'not making personal comments').")
                evidence.append("Gaslighting or persistent invalidation following a participant's explicit objection.")
                alt_interp = "Speaker may believe their criticism is factual, but disregarding explicit boundaries maintains interpersonal hostility."
                action = "Encourage objective dialogue and emphasize that personal boundaries must be respected."
                return (
                    "Potentially Harmful",
                    0.74,
                    "Moderate",
                    "Boundary Invalidation / Dismissive Gaslighting",
                    evidence,
                    alt_interp,
                    action,
                    signals
                )

        # ----------------------------------------------------
        # RULE 7.5: Defender Challenge / Silencing a Bystander
        # Aggressor tries to silence someone who is standing up for the victim.
        # "Mind your own business", "Nobody asked you", "Why are you always taking Sam's side?".
        # ----------------------------------------------------
        if feat.has_defender_challenge:
            had_prior_bystander = any(f.has_bystander_defense for f in prior_features)
            evidence.append("Speaker is attempting to silence or dismiss a bystander who was defending another participant ('Why are you always taking their side?', 'Nobody asked you').")
            if had_prior_bystander:
                evidence.append("Directly follows a bystander defence; the speaker is actively suppressing pro-social intervention.")
            alt_interp = "Could be dismissiveness rather than intentional silencing, but in the context of ongoing hostility it reinforces the hostile dynamic."
            action = "Monitor the pattern. Silencing bystanders is a common escalation tactic in group harassment."
            return (
                "Potentially Harmful",
                0.72,
                "Moderate",
                "Defender Challenge / Bystander Silencing",
                evidence,
                alt_interp,
                action,
                signals
            )

        # ----------------------------------------------------
        # RULE 7.8: Explicit Directed Verbal Abuse
        # Short transcripts reduce certainty about intent, but do not erase
        # observable directed abuse. Banter, reporting and protective rules
        # above still take precedence; physical threats are handled first.
        if feat.has_direct_abuse:
            evidence.append("Explicit second-person insult or directed profane abuse detected.")
            evidence.append("A short conversation does not make the abusive wording itself ambiguous.")
            return (
                "Potentially Harmful",
                0.85,
                "High",
                "Explicit Directed Verbal Abuse",
                evidence,
                "Intent and relationship history may be unclear; this wording is still directly abusive.",
                "Review the exchange and ask participants to stop the personal abuse. Check for threats and escalation.",
                signals,
            )

        # ----------------------------------------------------
        # RULE 8: Sarcasm & Incomplete Context / Ambiguity
        # Covers both sarcasm-praise markers ("real genius") and pure
        # direct-insult lexicon without any playful tone.
        # ----------------------------------------------------
        if feat.has_sarcasm_praise or (feat.has_insult and not feat.has_laughter):
            signals.is_sarcasm_suspect = True
            if feat.has_insult and not feat.has_sarcasm_praise:
                evidence.append("Direct derogatory language or insult detected without playful tone markers.")
            else:
                evidence.append("Apparent hyperbolic praise or critical phrase ('genius', 'cool', etc.) lacking explicit positive markers.")

            if next_feat and next_feat.has_protest:
                evidence.append(f"Interlocutor responded with confusion or distress ('{next_msg.text}'), indicating potential negative emotional impact.")
                alt_interp = "Could be deadpan humor between close peers, but the interlocutor's reaction demonstrates ambiguity or tension."
                action = "Clarify intent directly with the sender. Ambiguous sarcasm often escalates misunderstandings if left unaddressed."
                return (
                    "Potentially Harmful",
                    0.72,
                    "Moderate",
                    "Ambiguous Sarcasm / Passive Hostility",
                    evidence,
                    alt_interp,
                    action,
                    signals
                )
            
            if total_msgs <= 3 or (next_msg and "forget it" in next_msg.text.lower()):
                evidence.append("Conversation is brief or ended abruptly without resolving intent.")
                alt_interp = "Could be harmless dry sarcasm, friendly teasing without emojis, or genuine veiled mockery. Text alone is insufficient."
                action = "Ask for more conversational context or voice tone before concluding malicious intent."
                return (
                    "Uncertain — More Context Needed",
                    0.58,
                    "Low / Uncertain",
                    "Ambiguous Sarcasm / Incomplete Context",
                    evidence,
                    alt_interp,
                    action,
                    signals
                )

            if prior_hostile_count == 0:
                evidence.append("Single critical or sarcastic utterance without evidence of systematic targeting.")
                alt_interp = "Could be standard banter or momentary irritation between equals."
                action = "Monitor conversation to see if targeting repeats or if participant objects."
                return (
                    "Potentially Harmful",
                    0.65,
                    "Moderate",
                    "Isolated Critical Utterance",
                    evidence,
                    alt_interp,
                    action,
                    signals
                )
            else:
                evidence.append(f"Occurs within a pattern of repeated hostile turns ({prior_hostile_count} prior negative turns).")
                alt_interp = "Could be construed as mutual friction, but asymmetric repetition elevates concern."
                action = "Intervene to prevent continued targeting."
                return (
                    "Possible Cyberbullying",
                    0.83,
                    "High",
                    "Targeted Belittling / Mockery",
                    evidence,
                    alt_interp,
                    action,
                    signals
                )

        # ----------------------------------------------------
        # RULE 9: General Interlocutor Protest / Distress
        # ----------------------------------------------------
        if feat.has_protest:
            signals.is_victim_protest = True
            evidence.append("Speaker expresses uncertainty, objection, or distress at prior statements.")
            alt_interp = "May indicate genuine boundary setting, rhetorical questioning, or playful mock-indignation."
            action = "Validate the speaker's feelings and allow clarification before conflict escalates."
            return (
                "Uncertain — More Context Needed",
                0.62,
                "Moderate",
                "Boundary Inquiry / Objection",
                evidence,
                alt_interp,
                action,
                signals
            )

        # ----------------------------------------------------
        # RULE 10: Harmless / Neutral Baseline
        # ----------------------------------------------------
        evidence.append("Standard conversational turn without aggressive, exclusionary, or threatening indicators.")
        alt_interp = "Context appears neutral, though subtle offline in-jokes or coded slurs could remain invisible."
        action = "No action necessary."
        return (
            "Harmless / Neutral",
            0.92,
            "High",
            "Neutral Informational Exchange",
            evidence,
            alt_interp,
            action,
            signals
        )

    def _synthesize_risk(
        self,
        total_msgs: int,
        harmful_count: int,
        cyberbullying_count: int,
        threat_count: int,
        uncertain_count: int,
        banter_count: int,
        targeting_interactions: List[TargetingInteraction],
        is_known_friendly: bool,
        has_direct_lethal_threat: bool,
        has_confrontation_threat: bool,
        has_retaliatory_escalation: bool,
        has_boundary_fear: bool,
        has_bystander_defense: bool = False,
        has_stop_request: bool = False
    ) -> Tuple[str, float, str, List[str]]:
        """
        Synthesizes conversation-wide metrics into an explainable overall risk assessment.
        Transparently separates critical lethal danger from high-risk confrontation threats.
        """
        recommendations: List[str] = []

        # 1. Critical Risk: Explicit Physical Violence / Lethal Threats
        # Appropriately conservative: reserved for explicit severe harm/death threats
        if has_direct_lethal_threat:
            overall_risk = "Critical"
            risk_score = 92.0 + min(threat_count * 2.0, 7.0)
            summary = (
                f"Critical safety concern detected: {threat_count} turn(s) contain explicit violent, physical, "
                "or lethal threat phrasing ('hurt', 'kill', etc.). Immediate safety protocols and emergency/authorities reporting required."
            )
            recommendations.append("Ensure immediate physical safety of targeted individuals.")
            recommendations.append("Preserve original screenshots, message timestamps, and user handles.")
            recommendations.append("Report immediately to designated safeguarding leads, school/campus authorities, or emergency services.")
            return overall_risk, min(risk_score, 99.0), summary, recommendations

        # 2. High Risk: Real-World In-Person Confrontation Threat & Intimidation Escalation
        # Captures threats involving future location/time, retaliatory escalation following a complaint, or persistence after boundary assertion
        if has_confrontation_threat or (threat_count >= 1 and (has_retaliatory_escalation or has_boundary_fear)) or threat_count >= 2:
            overall_risk = "High"
            bonus = min(threat_count * 2.5, 5.0) + (2.5 if has_boundary_fear else 0.0) + (2.0 if has_retaliatory_escalation else 0.0)
            risk_score = min(88.0, 80.0 + bonus)
            summary = (
                f"High risk of real-world confrontation and harassment detected: {threat_count} turn(s) specify in-person targeting "
                "or persistent intimidation following an abuse grievance. Immediate institutional review and protective measures are advised."
            )
            recommendations.append("Ensure physical safety and avoid isolated areas during specified timeframes (e.g. after college or work).")
            recommendations.append("Preserve original screenshots, message timestamps, and user handles.")
            recommendations.append("Report immediately to college administration, campus security, or local safeguarding officers.")
            recommendations.append("Enforce strict no-contact boundaries between participants.")
            return overall_risk, min(risk_score, 89.0), summary, recommendations

        # 3. High Risk: Repeated Asymmetric Cyberbullying / Systematic Exclusion
        has_asymmetric_repetition = any(
            t.is_asymmetric and (t.harmful_turns >= 3 or (cyberbullying_count >= 1 and t.harmful_turns >= 2))
            for t in targeting_interactions
        )
        if cyberbullying_count >= 2 or has_asymmetric_repetition:
            overall_risk = "High"
            risk_score = 75.0 + min(cyberbullying_count * 5.0, 15.0)
            summary = (
                f"High risk of cyberbullying identified: {cyberbullying_count} turn(s) exhibit repeated targeting, "
                "systematic social exclusion, or unreciprocated harassment directed at specific participant(s)."
            )
            recommendations.append("Address the repeated targeting pattern rather than treating turns as isolated incidents.")
            recommendations.append("Provide a safe avenue for the targeted individual to express their boundaries.")
            recommendations.append("Apply group moderation or peer mediation according to community standards.")
            return overall_risk, min(risk_score, 89.0), summary, recommendations

        # 4. Moderate Risk: Isolated Hostile Turn, Single Retaliatory Warning, or Ambiguous Sarcasm with Distress
        if harmful_count > 0 or has_retaliatory_escalation or (cyberbullying_count == 1 and not has_asymmetric_repetition):
            overall_risk = "Moderate"
            risk_score = 45.0 + (harmful_count * 6.0)
            summary = (
                f"Moderate concern: {harmful_count} potentially harmful turn(s) identified. "
                "Evidence does not currently demonstrate persistent repeated confrontation, but tone warrants monitoring."
            )
            recommendations.append("Check in with the targeted participant to confirm whether the interaction felt hurtful.")
            recommendations.append("Encourage clear communication to clarify ambiguous or sarcastic statements.")
            recommendations.append("Monitor future exchanges for recurring conflict.")
            return overall_risk, min(risk_score, 68.0), summary, recommendations

        # 4.5. Moderate Risk: Protective Intervention or Unresolved Boundary Protest
        # Guardrail: If a third-party bystander had to intervene to protect someone,
        # or a participant asserted a boundary/stop request, and there is no reciprocal banter,
        # the exchange cannot be silently dismissed as "Low Risk / Safe Interaction".
        has_protective_or_stop = (has_bystander_defense or has_stop_request or has_boundary_fear)
        if has_protective_or_stop and banter_count == 0:
            overall_risk = "Moderate"
            risk_score = 48.0 + min(harmful_count * 5.0, 15.0)
            summary = (
                "Moderate concern — Interpersonal boundary conflict detected: A participant asserted explicit boundaries "
                "or a bystander intervened to de-escalate tension. Tone warrants human discernment and moderation monitoring."
            )
            recommendations.append("Acknowledge bystander intervention and confirm that personal boundaries are respected.")
            recommendations.append("Check in with the targeted participant regarding recurring friction.")
            recommendations.append("Monitor future exchanges to ensure hostility does not persist.")
            return overall_risk, min(risk_score, 68.0), summary, recommendations

        # 5. Low Risk: Uncertain / Ambiguous Context
        if uncertain_count > 0 and banter_count == 0:
            overall_risk = "Low"
            risk_score = 22.0 + (uncertain_count * 4.0)
            summary = (
                f"Low-to-moderate uncertainty: {uncertain_count} turn(s) contain ambiguous phrases where intent "
                "cannot be reliably inferred without wider conversational history or voice tone."
            )
            recommendations.append("Gather additional conversational turns before reaching conclusions.")
            recommendations.append("Avoid premature disciplinary actions based on isolated ambiguous remarks.")
            return overall_risk, min(risk_score, 38.0), summary, recommendations

        # 6. Low Risk: Friendly Banter / Neutral
        overall_risk = "Low"
        risk_score = max(5.0, 14.0 - (banter_count * 2.0))
        if banter_count > 0:
            summary = (
                f"Low risk — Healthy conversational interaction detected: {banter_count} turn(s) demonstrate "
                "reciprocal banter, laughter, and mutual participation without persistent hostile targeting."
            )
            recommendations.append("No disciplinary or moderation intervention recommended.")
            recommendations.append("Continue to foster a supportive and respectful group culture.")
        else:
            summary = "Low risk — Routine, neutral communication with no concerning toxicity, exclusion, or intimidation detected."
            recommendations.append("Standard interaction. No action required.")

        return overall_risk, round(risk_score, 1), summary, recommendations

    def _empty_response(self, context: Optional[ContextInfo]) -> AnalyzeResponse:
        return AnalyzeResponse(
            conversation_summary="No valid conversation turns detected. Please enter dialogue in 'Speaker: Message' format.",
            overall_risk="Low",
            risk_score=0.0,
            confidence="High",
            metrics=ConversationMetrics(
                total_messages=0,
                potentially_harmful_count=0,
                uncertain_count=0,
                friendly_banter_count=0,
                neutral_count=0,
                threat_count=0,
                participant_count=0
            ),
            messages=[],
            participants=[],
            targeting_patterns=[],
            recommendations=["Enter or paste a conversation to begin analysis."],
            model_info=ModelInfo(
                engine_name="ContextGuard Local Contextual NLP Pipeline",
                engine_type="Hybrid Context-Aware Rule & NLP Engine",
                execution_mode="Active Local Pipeline",
                description="Modular dialogue analysis system.",
                transparency_notes="Awaiting input dialogue."
            ),
            limitations=["Empty input provides no context for analysis."]
        )
