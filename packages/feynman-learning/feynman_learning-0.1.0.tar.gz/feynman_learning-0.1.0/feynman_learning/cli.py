"""
Command-line interface for feynman-learning
"""

import argparse
import sys
import os
from typing import Optional

from .core import FeynmanLearner
from .ai_explainer import AIExplainer, OpenAICompatibleProvider
from .session_manager import SessionManager
from .config import get_config_manager, reset_config_manager


def create_ai_provider(provider_name: str, api_key: str, model: Optional[str] = None, base_url: Optional[str] = None, organization: Optional[str] = None):
    """Create an AI provider based on the provider name"""
    if provider_name.lower() == "openai":
        return OpenAICompatibleProvider(
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1",
            model=model or "gpt-3.5-turbo",
            organization=organization
        )
    elif provider_name.lower() in ["local", "compatible", "custom"]:
        return OpenAICompatibleProvider(
            api_key=api_key or "dummy-key",
            base_url=base_url or "http://localhost:8000/v1",
            model=model or "gpt-3.5-turbo"
        )
    else:
        raise ValueError(f"Unsupported provider: {provider_name}. Supported: openai, local, compatible, custom")


def setup_ai_provider(provider_name: str, config, use_saved_config: bool = False):
    """Setup AI provider using configuration or user input"""
    if provider_name == "openai":
        # Get saved configuration
        saved_api_key = config.get("ai_provider.api_key", "")
        saved_model = config.get("ai_provider.model", "gpt-3.5-turbo")
        saved_organization = config.get("ai_provider.organization", "")
        
        if use_saved_config and saved_api_key:
            # Use saved configuration directly
            api_key = saved_api_key
            model = saved_model
            organization = saved_organization or None
        else:
            # Prompt for configuration
            if not saved_api_key:
                api_key = input("Enter your OpenAI API key: ").strip()
            else:
                use_saved_key = input(f"Use saved API key ({saved_api_key[:8]}...)? (y/n): ").strip().lower()
                if use_saved_key in ['y', 'yes', '']:
                    api_key = saved_api_key
                else:
                    api_key = input("Enter your OpenAI API key: ").strip()
            
            if not api_key:
                print("No API key provided. Running without AI assistance.")
                return FeynmanLearner()
            
            model = input(f"Model (default: {saved_model}): ").strip() or saved_model
            organization = input(f"Organization ID (optional, default: {saved_organization or 'none'}): ").strip() or saved_organization or None
            
            # Save configuration
            config.set_ai_provider_config("openai", api_key=api_key, model=model, organization=organization)
            config.save_config()
        
        try:
            provider = create_ai_provider(provider_name, api_key, model, "https://api.openai.com/v1", organization)
            ai_explainer = AIExplainer(provider)
            print("✅ AI assistance enabled with OpenAI")
            return FeynmanLearner(ai_explainer)
        except Exception as e:
            print(f"❌ Error setting up AI: {e}")
            print("Continuing without AI assistance.")
            return FeynmanLearner()
    
    elif provider_name == "local":
        # Get saved configuration
        saved_base_url = config.get("ai_provider.base_url", "http://localhost:8000/v1")
        saved_model = config.get("ai_provider.model", "gpt-3.5-turbo")
        saved_api_key = config.get("ai_provider.api_key", "dummy-key")
        
        if use_saved_config:
            # Use saved configuration directly
            base_url = saved_base_url
            model = saved_model
            api_key = saved_api_key
        else:
            # Prompt for configuration
            base_url = input(f"Base URL (default: {saved_base_url}): ").strip() or saved_base_url
            model = input(f"Model name (default: {saved_model}): ").strip() or saved_model
            api_key = input(f"API key (default: {saved_api_key}): ").strip() or saved_api_key
            
            # Save configuration
            config.set_ai_provider_config("local", base_url=base_url, model=model, api_key=api_key)
            config.save_config()
        
        try:
            provider = create_ai_provider(provider_name, api_key, model, base_url)
            ai_explainer = AIExplainer(provider)
            print("✅ AI assistance enabled with local/compatible endpoint")
            return FeynmanLearner(ai_explainer)
        except Exception as e:
            print(f"❌ Error setting up AI: {e}")
            print("Continuing without AI assistance.")
            return FeynmanLearner()
    
    else:
        # Save "none" preference to avoid asking again
        config.set_ai_provider_config("none")
        config.save_config()
        print("Running without AI assistance.")
        return FeynmanLearner()


def interactive_learning_session():
    """Run an interactive learning session"""
    print("=== Feynman Learning Interactive Session ===\n")
    
    config = get_config_manager()
    
    # Check if configuration file exists
    if not config.config_path.exists():
        print("👋 Welcome to Feynman Learning!")
        print("Let's set up your configuration first...\n")
        interactive_config_setup()
        print("\n🎯 Now let's start your learning session!\n")
        # Reload config after setup
        reset_config_manager()
        config = get_config_manager()
    
    # Check if we have a valid saved configuration
    saved_provider = config.get("ai_provider.type", "")
    has_saved_config = saved_provider in ["openai", "local"]
    
    if has_saved_config:
        provider_name = saved_provider
        print(f"Using saved {saved_provider} configuration...")
        # Show tip only if enabled in display settings
        if config.get("display.show_tips", True):
            print("💡 To change configuration, run: feynman-learning config setup")
        use_saved = True
    else:
        provider_name = input("AI Provider (openai/local/none): ").strip().lower()
        use_saved = False
    
    # Setup AI provider
    learner = setup_ai_provider(provider_name, config, use_saved)
    
    # Start session manager
    session_manager = SessionManager()
    
    # Get concept to learn
    concept_name = input("\nWhat concept would you like to learn? ").strip()
    if not concept_name:
        print("No concept provided. Exiting.")
        return
    
    concept_content = input(f"Enter content/description for '{concept_name}': ").strip()
    if not concept_content:
        print("No content provided. Exiting.")
        return
    
    # Add concept and start session
    concept = learner.add_concept(concept_name, concept_content)
    session_id = session_manager.start_session(concept_name, concept.mastery_score)
    
    print(f"\n🎯 Starting learning session: {session_id}")
    print("=" * 50)
    
    # Phase 1: Study
    print("\n📚 PHASE 1: STUDY")
    print("-" * 20)
    try:
        content = learner.study_concept(concept_name)
        print(content)
        session_manager.update_phase("study")
        input("\nPress Enter to continue to explanation phase...")
    except Exception as e:
        print(f"Error in study phase: {e}")
    
    # Phase 2: Explain
    print("\n🗣️  PHASE 2: EXPLAIN")
    print("-" * 20)
    default_audience = config.get("session.default_target_audience", "beginner")
    target_audience = input(f"Who are you explaining this to? (default: {default_audience}): ").strip() or default_audience
    
    try:
        explanation = learner.explain_concept(concept_name, target_audience)
        print(f"\nExplanation for {target_audience}:")
        print(explanation)
        session_manager.add_note(f"Explained to {target_audience}")
        session_manager.update_phase("explain")
        input("\nPress Enter to continue to gap identification...")
    except Exception as e:
        print(f"Error in explanation phase: {e}")
    
    # Phase 3: Identify Gaps
    print("\n🔍 PHASE 3: IDENTIFY GAPS")
    print("-" * 25)
    try:
        gaps = learner.identify_knowledge_gaps(concept_name)
        if gaps:
            print("Knowledge gaps identified:")
            for i, gap in enumerate(gaps, 1):
                print(f"{i}. {gap}")
        else:
            print("No significant gaps identified!")
        session_manager.add_note(f"Identified {len(gaps)} gaps")
        session_manager.update_phase("identify_gaps")
        input("\nPress Enter to continue to improvement phase...")
    except Exception as e:
        print(f"Error in gap identification: {e}")
    
    # Phase 4: Improve
    print("\n🚀 PHASE 4: IMPROVE EXPLANATION")
    print("-" * 30)
    try:
        improved = learner.improve_explanation(concept_name)
        print("Improved explanation:")
        print(improved)
        session_manager.add_note("Generated improved explanation")
        session_manager.update_phase("simplify")
        input("\nPress Enter to continue to review phase...")
    except Exception as e:
        print(f"Error in improvement phase: {e}")
    
    # Phase 5: Review
    print("\n📊 PHASE 5: REVIEW")
    print("-" * 18)
    try:
        progress = learner.review_concept(concept_name)
        print("Learning Progress:")
        print(f"  Concept: {progress['concept']}")
        print(f"  Mastery Score: {progress['mastery_score']:.1%}")
        print(f"  Gaps Found: {progress['gaps_count']}")
        print(f"  Explanations Created: {progress['explanations_count']}")
        
        if progress['next_steps']:
            print("  Next Steps:")
            for step in progress['next_steps']:
                print(f"    • {step}")
        
        session_manager.update_phase("review")
        session_manager.end_session(progress['mastery_score'])
        
    except Exception as e:
        print(f"Error in review phase: {e}")
        session_manager.end_session(0.5)  # Default score
    
    # Final statistics
    print("\n" + "=" * 50)
    print("🎉 SESSION COMPLETE!")
    stats = session_manager.get_learning_statistics()
    print(f"📈 Total learning time: {stats['total_time_minutes']} minutes")
    print(f"🔥 Learning streak: {stats['learning_streak_days']} days")
    
    # Suggestions
    suggestion = session_manager.suggest_next_session()
    print(f"\n💡 Next suggestion: {suggestion['suggestion']}")
    print(f"   Reason: {suggestion['reason']}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="AI-powered learning using the Feynman Technique"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Interactive session command
    interactive_parser = subparsers.add_parser(
        "learn", 
        help="Start an interactive learning session"
    )
    
    # Stats command
    stats_parser = subparsers.add_parser(
        "stats",
        help="Show learning statistics"
    )
    
    # Progress command
    progress_parser = subparsers.add_parser(
        "progress",
        help="Show progress for a specific concept"
    )
    progress_parser.add_argument("concept", help="Concept name")
    
    # Export command
    export_parser = subparsers.add_parser(
        "export",
        help="Export learning progress report"
    )
    export_parser.add_argument("-o", "--output", default="learning_report.json", help="Output file path")
    
    # Config command
    config_parser = subparsers.add_parser(
        "config",
        help="Manage configuration settings"
    )
    config_subparsers = config_parser.add_subparsers(dest="config_action", help="Configuration actions")
    
    # Config show
    config_subparsers.add_parser("show", help="Show current configuration")
    
    # Config set
    config_set_parser = config_subparsers.add_parser("set", help="Set configuration value")
    config_set_parser.add_argument("key", help="Configuration key (e.g., ai_provider.type)")
    config_set_parser.add_argument("value", help="Configuration value")
    
    # Config reset
    config_subparsers.add_parser("reset", help="Reset configuration to defaults")
    
    # Config setup
    config_subparsers.add_parser("setup", help="Interactive configuration setup")
    
    args = parser.parse_args()
    
    if args.command == "learn":
        interactive_learning_session()
    
    elif args.command == "stats":
        session_manager = SessionManager()
        stats = session_manager.get_learning_statistics()
        
        print("📊 Learning Statistics")
        print("=" * 30)
        print(f"Total Sessions: {stats['total_sessions']}")
        print(f"Total Time: {stats['total_time_minutes']} minutes")
        print(f"Concepts Studied: {stats['concepts_studied']}")
        print(f"Average Session Time: {stats['average_session_time']:.1f} minutes")
        print(f"Average Mastery Improvement: {stats['mastery_improvement']:.1%}")
        print(f"Most Studied Concept: {stats['most_studied_concept']}")
        print(f"Learning Streak: {stats['learning_streak_days']} days")
        
        if stats.get('concept_breakdown'):
            print("\nConcept Breakdown:")
            for concept, count in stats['concept_breakdown'].items():
                print(f"  {concept}: {count} sessions")
    
    elif args.command == "progress":
        session_manager = SessionManager()
        progress = session_manager.get_concept_progress(args.concept)
        
        print(f"📈 Progress for '{args.concept}'")
        print("=" * 40)
        print(f"Sessions: {progress['sessions_count']}")
        print(f"Total Time: {progress['total_time_minutes']} minutes")
        print(f"Current Mastery: {progress['current_mastery']:.1%}")
        print(f"Phases Completed: {', '.join(progress['phases_completed'])}")
        
        if progress['last_session']:
            print(f"Last Session: {progress['last_session']}")
        
        if progress['mastery_trend']:
            print("\nMastery Trend:")
            for date, mastery in progress['mastery_trend'][-5:]:  # Last 5 sessions
                print(f"  {date[:10]}: {mastery:.1%}")
    
    elif args.command == "export":
        session_manager = SessionManager()
        output_path = session_manager.export_progress_report(args.output)
        print(f"✅ Progress report exported to: {output_path}")
    
    elif args.command == "config":
        handle_config_command(args)
    
    else:
        parser.print_help()


def handle_config_command(args):
    """Handle configuration management commands"""
    config = get_config_manager()
    
    if args.config_action == "show":
        print("📋 Current Configuration")
        print("=" * 30)
        print(config.show_config())
        print(f"\nConfig file: {config.config_path}")
    
    elif args.config_action == "set":
        try:
            # Convert string values to appropriate types
            value = args.value
            if value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)
            elif value.replace('.', '').isdigit():
                value = float(value)
            
            config.set(args.key, value)
            if config.save_config():
                print(f"✅ Set {args.key} = {value}")
            else:
                print(f"❌ Failed to save configuration")
        except Exception as e:
            print(f"❌ Error setting configuration: {e}")
    
    elif args.config_action == "reset":
        confirm = input("Are you sure you want to reset all configuration to defaults? (y/n): ").strip().lower()
        if confirm in ['y', 'yes']:
            config.reset_to_defaults()
            if config.save_config():
                print("✅ Configuration reset to defaults")
            else:
                print("❌ Failed to save configuration")
        else:
            print("Operation cancelled")
    
    elif args.config_action == "setup":
        interactive_config_setup()
    
    else:
        print("Available config actions: show, set, reset, setup")


def interactive_config_setup():
    """Interactive configuration setup"""
    print("=== Feynman Learning Configuration Setup ===\n")
    
    config = get_config_manager()
    
    # AI Provider setup
    print("🤖 AI Provider Configuration")
    print("-" * 30)
    current_provider = config.get("ai_provider.type", "openai")
    provider_type = input(f"AI Provider type (openai/local/none) [current: {current_provider}]: ").strip() or current_provider
    
    if provider_type == "openai":
        current_api_key = config.get("ai_provider.api_key", "")
        if current_api_key:
            api_key = input(f"OpenAI API key [current: {current_api_key[:8]}...]: ").strip() or current_api_key
        else:
            api_key = input("OpenAI API key: ").strip()
        
        current_model = config.get("ai_provider.model", "gpt-3.5-turbo")
        model = input(f"Model [current: {current_model}]: ").strip() or current_model
        
        current_organization = config.get("ai_provider.organization", "")
        organization = input(f"Organization ID (optional) [current: {current_organization or 'none'}]: ").strip()
        if organization.lower() == 'none':
            organization = ""
        elif not organization:
            organization = current_organization
        
        config.set_ai_provider_config("openai", api_key=api_key, model=model, organization=organization)
    
    elif provider_type == "local":
        current_base_url = config.get("ai_provider.base_url", "http://localhost:8000/v1")
        base_url = input(f"Base URL [current: {current_base_url}]: ").strip() or current_base_url
        
        current_model = config.get("ai_provider.model", "gpt-3.5-turbo")
        model = input(f"Model name [current: {current_model}]: ").strip() or current_model
        
        current_api_key = config.get("ai_provider.api_key", "dummy-key")
        api_key = input(f"API key [current: {current_api_key}]: ").strip() or current_api_key
        
        config.set_ai_provider_config("local", base_url=base_url, model=model, api_key=api_key)
    
    else:
        config.set_ai_provider_config("none")
    
    # Session preferences
    print("\n📚 Session Preferences")
    print("-" * 20)
    current_audience = config.get("session.default_target_audience", "beginner")
    audience = input(f"Default target audience [current: {current_audience}]: ").strip() or current_audience
    config.set("session.default_target_audience", audience)
    
    # Learning preferences
    print("\n🎯 Learning Preferences")
    print("-" * 22)
    current_mastery = config.get("learning.min_mastery_score", 0.7)
    mastery_input = input(f"Minimum mastery score (0.0-1.0) [current: {current_mastery}]: ").strip()
    if mastery_input:
        try:
            mastery = float(mastery_input)
            if 0.0 <= mastery <= 1.0:
                config.set("learning.min_mastery_score", mastery)
            else:
                print("Invalid mastery score, keeping current value")
        except ValueError:
            print("Invalid mastery score, keeping current value")
    
    # Display preferences
    print("\n🎨 Display Preferences")
    print("-" * 20)
    current_tips = config.get("display.show_tips", True)
    show_tips = input(f"Show helpful tips (true/false) [current: {current_tips}]: ").strip()
    if show_tips.lower() in ['true', 'false']:
        config.set("display.show_tips", show_tips.lower() == 'true')
    
    # Save configuration
    if config.save_config():
        print("\n✅ Configuration saved successfully!")
        print(f"Config file: {config.config_path}")
    else:
        print("\n❌ Failed to save configuration")


if __name__ == "__main__":
    main()