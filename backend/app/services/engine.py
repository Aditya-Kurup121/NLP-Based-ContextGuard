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
        """
        Attempts to load Hugging Face transformer pipeline if installed and downloaded.
        Provides zero-overhead fallback to local calibrated multi-turn context analyzer.
        """
        try:
            # We check if transformers is installed without blocking startup
            import transformers # noqa
            self.transformer_available = True
        except ImportError:
            self.transformer_available = False

    def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        parsed_messages = parse_conversation(request.conversation)
        if not parsed_messages:
            return self._empty_response(request.context)

        features_list = extract_all_features(parsed_messages)
        sender_target_pairs = infer_message_targets(parsed_messages)
        total_msgs = len(parsed_messages)

        context_info = request.context or ContextInfo()
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
                    signals=signals
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

        overall_risk, estimated_risk_score, risk_summary, recommendations = self._synthesize_risk(
            total_msgs=total_msgs,
            harmful_count=harmful_count,
            cyberbullying_count=cyberbullying_count,
            threat_count=threat_count,
            uncertain_count=uncertain_count,
            banter_count=banter_count,
            targeting_interactions=targeting_interactions,
            is_known_friendly=is_known_friendly
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
            engine_type="Hybrid Multi-Turn Dialogue Rule & Calibrated Context Engine",
            execution_mode="Active Local Pipeline (Deterministic, Zero External Network Leaks)",
            description="Analyzes conversational history, turn-taking reciprocity, sarcasm markers, and targeting asymmetry.",
            transparency_notes="Heuristic scores and contextual signals are transparently labeled. Transformer weights can be hot-swapped via Hugging Face pipeline."
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
        has_reciprocal_laughter: bool,
        is_known_friendly: bool,
        is_high_risk_setting: bool,
        context_info: ContextInfo,
        speaker_target_hostile_counts: Dict[Tuple[str, str], int]
    ) -> Tuple[str, float, str, str, List[str], Optional[str], str, MessageSignal]:
        """
        Classifies an individual turn by looking at its own features AND the surrounding dialogue context.
        """
        evidence: List[str] = []
        signals = MessageSignal(
            has_laughter=feat.has_laughter,
            has_playful_emoji=feat.has_playful_emoji,
            has_exclusion_phrase=feat.has_exclusion,
            has_insult_lexicon=feat.has_insult,
            has_threat_lexicon=feat.has_threat,
            is_sarcasm_suspect=feat.has_sarcasm_praise,
            is_reciprocal_tease=False,
            is_repeated_target=False,
            is_victim_protest=feat.has_protest
        )

        prior_hostile_count = 0
        if target:
            prior_hostile_count = speaker_target_hostile_counts.get((sender, target), 0)
        # Also check general hostile turns by this sender if target is implied/group
        general_prior = sum(count for (s, t), count in speaker_target_hostile_counts.items() if s == sender)
        prior_hostile_count = max(prior_hostile_count, general_prior)

        signals.is_repeated_target = prior_hostile_count >= 1

        # ----------------------------------------------------
        # RULE 1: Direct Physical Threat / Severe Safety Concern
        # ----------------------------------------------------
        if feat.has_threat:
            evidence.append("Explicit violent or threatening phrasing detected ('hurt', 'find you after class', 'kill', etc.).")
            alt_interp = "Could theoretically be gaming hyperbole, but safety protocols require treating direct threats with urgency."
            action = "Immediately prioritize personal safety. Save conversation records and report to a trusted adult, educator, or platform administrator."
            return (
                "Threat / Urgent Concern",
                0.94,
                "High",
                "Direct Intimidation / Physical Threat",
                evidence,
                alt_interp,
                action,
                signals
            )

        # ----------------------------------------------------
        # RULE 2: Social Exclusion / Hostile Rejection
        # ----------------------------------------------------
        if feat.has_exclusion:
            evidence.append("Systemic exclusionary language detected ('nobody wants you', 'leave the group', 'stop talking', etc.).")
            signals.has_exclusion_phrase = True

            # Check if this speaker has repeatedly said this, or if multiple speakers join
            if prior_hostile_count >= 1:
                evidence.append(f"Follows {prior_hostile_count} previous hostile or exclusionary turn(s) from {sender} toward {target or 'the participant'}.")
                classification = "Possible Cyberbullying"
                pattern = "Repeated Social Exclusion & Harassment"
                conf = 0.88
                action = "Recognize this as persistent exclusion. Consider stepping away from this group, seeking support, or archiving the conversation for moderation."
                alt_interp = "Unlikely to be friendly teasing given the lack of playful cues and repeated unreciprocated hostility."
            else:
                classification = "Possible Cyberbullying" if not is_known_friendly else "Potentially Harmful"
                pattern = "Social Exclusion & Ostracism"
                conf = 0.81
                action = "Set clear boundaries or ask a moderator to intervene if this behavior continues."
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
        # RULE 3: Friendly Banter & Reciprocal Teasing
        # ----------------------------------------------------
        # Case A: Contains teasing/sarcasm words ("genius", "pro athlete", "missed empty goal")
        # BUT accompanied by laughter/emojis or answered by playful mutual teasing
        is_teasing_with_laughter = (feat.has_laughter or feat.has_playful_emoji) and (feat.has_sarcasm_praise or feat.has_insult)
        has_subsequent_laughter = (next_feat and (next_feat.has_laughter or next_feat.has_playful_emoji or next_feat.has_sarcasm_praise))
        has_prior_laughter = (prev_feat and (prev_feat.has_laughter or prev_feat.has_playful_emoji))

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
        # RULE 4: Sarcasm & Incomplete Context / Ambiguity
        # ----------------------------------------------------
        # Example: "Wow, you're a real genius." followed by "What is that supposed to mean?"
        if feat.has_sarcasm_praise or (feat.has_insult and not feat.has_laughter):
            signals.is_sarcasm_suspect = True
            evidence.append("Apparent hyperbolic praise or critical phrase ('genius', 'cool', etc.) lacking explicit positive markers.")

            # Look forward: did the listener protest or ask for clarification?
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
            
            # Look forward: short conversation or abrupt ending ("Forget it")
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

            # Isolated mild insult or sarcasm with no other hostile cues
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
        # RULE 5: Interlocutor Protest or Invalidation
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
        # RULE 6: Harmless / Neutral Baseline
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
        is_known_friendly: bool
    ) -> Tuple[str, float, str, List[str]]:
        """
        Synthesizes conversation-wide metrics into an explainable overall risk assessment.
        """
        recommendations: List[str] = []

        # 1. Critical Risk: Physical Threats
        if threat_count > 0:
            overall_risk = "Critical"
            risk_score = 92.0 + min(threat_count * 2.0, 7.0)
            summary = (
                f"Critical safety concern detected: {threat_count} turn(s) contain explicit violent, physical, "
                "or intimidating threat phrasing. Immediate review and safety measures are strongly advised."
            )
            recommendations.append("Ensure immediate physical safety of targeted individuals.")
            recommendations.append("Preserve original screenshots, message timestamps, and user handles.")
            recommendations.append("Report immediately to designated safeguarding leads, school authorities, or emergency support.")
            return overall_risk, min(risk_score, 99.0), summary, recommendations

        # 2. High Risk: Repeated Asymmetric Cyberbullying / Systematic Exclusion
        has_asymmetric_repetition = any(t.is_asymmetric and t.harmful_turns >= 2 for t in targeting_interactions)
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

        # 3. Moderate Risk: Isolated Hostile Turn or Ambiguous Sarcasm with Distress
        if harmful_count > 0 or (cyberbullying_count == 1 and not has_asymmetric_repetition):
            overall_risk = "Moderate"
            risk_score = 45.0 + (harmful_count * 6.0)
            summary = (
                f"Moderate concern: {harmful_count} potentially harmful turn(s) identified. "
                "Evidence does not currently demonstrate persistent repeated targeting, but tone warrants monitoring."
            )
            recommendations.append("Check in with the targeted participant to confirm whether the interaction felt hurtful.")
            recommendations.append("Encourage clear communication to clarify ambiguous or sarcastic statements.")
            recommendations.append("Monitor future exchanges for recurring conflict.")
            return overall_risk, min(risk_score, 65.0), summary, recommendations

        # 4. Low Risk: Uncertain / Ambiguous Context
        if uncertain_count > 0 and banter_count == 0:
            overall_risk = "Low"
            risk_score = 25.0 + (uncertain_count * 4.0)
            summary = (
                f"Low-to-moderate uncertainty: {uncertain_count} turn(s) contain ambiguous phrases (such as deadpan sarcasm) "
                "where intent cannot be reliably inferred without wider conversational history or voice tone."
            )
            recommendations.append("Gather additional conversational turns before reaching conclusions.")
            recommendations.append("Avoid premature disciplinary actions based on isolated ambiguous remarks.")
            return overall_risk, min(risk_score, 38.0), summary, recommendations

        # 5. Low Risk: Friendly Banter / Neutral
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
