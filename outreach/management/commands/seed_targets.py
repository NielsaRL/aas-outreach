#list of targets for star parties, these are considered static targets

from django.core.management.base import BaseCommand
from outreach.models import AstronomicalTarget

DEFAULT_TARGETS = [
    # Winter / late fall
    {"name": "Orion Nebula", "target_type": "DSO", "constellation": "Orion", "best_months": ["12", "1", "2", "3"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Bright stellar nursery where new stars are forming."},
    {"name": "Running Man Nebula", "target_type": "DSO", "constellation": "Orion", "best_months": ["12", "1", "2", "3"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Reflection nebula near the Orion Nebula."},
    {"name": "Pleiades", "target_type": "DSO", "constellation": "Taurus", "best_months": ["11", "12", "1", "2", "3"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Open star cluster also called the Seven Sisters."},
    {"name": "Hyades", "target_type": "DSO", "constellation": "Taurus", "best_months": ["11", "12", "1", "2", "3"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Large nearby open cluster forming the face of Taurus."},
    {"name": "Double Cluster", "target_type": "DSO", "constellation": "Perseus", "best_months": ["10", "11", "12", "1", "2"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Two neighboring open clusters rich with young stars."},
    {"name": "M35", "target_type": "DSO", "constellation": "Gemini", "best_months": ["12", "1", "2", "3", "4"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Bright open cluster in Gemini."},
    {"name": "M36", "target_type": "DSO", "constellation": "Auriga", "best_months": ["12", "1", "2", "3"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Compact open cluster in Auriga."},
    {"name": "M37", "target_type": "DSO", "constellation": "Auriga", "best_months": ["12", "1", "2", "3"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Rich open cluster with many faint stars."},
    {"name": "M38", "target_type": "DSO", "constellation": "Auriga", "best_months": ["12", "1", "2", "3"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Open cluster sometimes described as cross-shaped."},
    {"name": "Beehive Cluster", "target_type": "DSO", "constellation": "Cancer", "best_months": ["1", "2", "3", "4", "5"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Large open cluster visible in binoculars and small telescopes."},
    {"name": "M67", "target_type": "DSO", "constellation": "Cancer", "best_months": ["2", "3", "4", "5"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Old open cluster with Sun-like stars."},
    {"name": "Eskimo Nebula", "target_type": "DSO", "constellation": "Gemini", "best_months": ["1", "2", "3", "4"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Planetary nebula useful for discussing the late life of stars."},
    {"name": "Sirius", "target_type": "OTHER", "constellation": "Canis Major", "best_months": ["12", "1", "2", "3"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Brightest star in the night sky."},
    {"name": "Betelgeuse", "target_type": "OTHER", "constellation": "Orion", "best_months": ["12", "1", "2", "3"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Red supergiant star in Orion."},
    {"name": "Rigel", "target_type": "OTHER", "constellation": "Orion", "best_months": ["12", "1", "2", "3"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Blue-white supergiant star in Orion."},
    {"name": "Aldebaran", "target_type": "OTHER", "constellation": "Taurus", "best_months": ["11", "12", "1", "2", "3"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Orange giant star marking the eye of Taurus."},
    {"name": "Capella", "target_type": "OTHER", "constellation": "Auriga", "best_months": ["11", "12", "1", "2", "3"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Bright star in Auriga, good for winter sky orientation."},
    {"name": "Orion", "target_type": "CONSTELLATION", "constellation": "Orion", "best_months": ["12", "1", "2", "3"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "One of the easiest constellations for the public to recognize."},
    {"name": "Taurus", "target_type": "CONSTELLATION", "constellation": "Taurus", "best_months": ["11", "12", "1", "2", "3"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Contains Aldebaran, the Hyades, and the Pleiades."},
    {"name": "Winter Hexagon", "target_type": "CONSTELLATION", "constellation": "", "best_months": ["12", "1", "2", "3"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Large winter asterism connecting several bright stars."},

    # Spring
    {"name": "Leo Triplet", "target_type": "DSO", "constellation": "Leo", "best_months": ["3", "4", "5"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Group of three galaxies; best under darker skies."},
    {"name": "M3", "target_type": "DSO", "constellation": "Canes Venatici", "best_months": ["3", "4", "5", "6"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Bright globular cluster of ancient stars."},
    {"name": "M53", "target_type": "DSO", "constellation": "Coma Berenices", "best_months": ["3", "4", "5", "6"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Globular cluster useful for discussing old star populations."},
    {"name": "Coma Star Cluster", "target_type": "DSO", "constellation": "Coma Berenices", "best_months": ["3", "4", "5", "6"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Large loose star cluster visible in binoculars."},
    {"name": "Sombrero Galaxy", "target_type": "DSO", "constellation": "Virgo", "best_months": ["3", "4", "5", "6"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Galaxy with a prominent dark dust lane."},
    {"name": "M81 Bode's Galaxy", "target_type": "DSO", "constellation": "Ursa Major", "best_months": ["2", "3", "4", "5"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Bright spiral galaxy in Ursa Major."},
    {"name": "M82 Cigar Galaxy", "target_type": "DSO", "constellation": "Ursa Major", "best_months": ["2", "3", "4", "5"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Starburst galaxy near M81."},
    {"name": "M51 Whirlpool Galaxy", "target_type": "DSO", "constellation": "Canes Venatici", "best_months": ["3", "4", "5", "6"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Interacting galaxy pair; best under darker skies."},
    {"name": "Big Dipper", "target_type": "CONSTELLATION", "constellation": "Ursa Major", "best_months": ["3", "4", "5", "6", "7"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Useful for finding Polaris and explaining circumpolar stars."},
    {"name": "Polaris", "target_type": "OTHER", "constellation": "Ursa Minor", "best_months": [], "visible_during_event": True, "discussion_only": True, "outreach_notes": "North Star; useful for explaining Earth’s rotation and navigation."},
    {"name": "Arcturus", "target_type": "OTHER", "constellation": "Boötes", "best_months": ["3", "4", "5", "6", "7"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Bright orange giant star; found by arcing from the Big Dipper."},
    {"name": "Cor Caroli", "target_type": "OTHER", "constellation": "Canes Venatici", "best_months": ["3", "4", "5", "6"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Pretty double star; good for small telescopes."},
    {"name": "Leo", "target_type": "CONSTELLATION", "constellation": "Leo", "best_months": ["3", "4", "5"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Spring constellation shaped like a lion."},
    {"name": "Virgo", "target_type": "CONSTELLATION", "constellation": "Virgo", "best_months": ["4", "5", "6"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Region rich with galaxies."},
    {"name": "Boötes", "target_type": "CONSTELLATION", "constellation": "Boötes", "best_months": ["4", "5", "6", "7"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Contains bright Arcturus."},

    # Summer
    {"name": "M13 Hercules Cluster", "target_type": "DSO", "constellation": "Hercules", "best_months": ["5", "6", "7", "8", "9"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Bright globular cluster with hundreds of thousands of stars."},
    {"name": "M92", "target_type": "DSO", "constellation": "Hercules", "best_months": ["5", "6", "7", "8", "9"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Globular cluster often overshadowed by M13 but still excellent."},
    {"name": "Ring Nebula", "target_type": "DSO", "constellation": "Lyra", "best_months": ["6", "7", "8", "9", "10"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Planetary nebula formed by a dying star shedding outer layers."},
    {"name": "Dumbbell Nebula", "target_type": "DSO", "constellation": "Vulpecula", "best_months": ["6", "7", "8", "9", "10"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Large planetary nebula; good for discussing stellar death."},
    {"name": "Wild Duck Cluster", "target_type": "DSO", "constellation": "Scutum", "best_months": ["6", "7", "8", "9"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Rich open cluster near the Milky Way."},
    {"name": "Lagoon Nebula", "target_type": "DSO", "constellation": "Sagittarius", "best_months": ["6", "7", "8", "9"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Bright emission nebula and star-forming region."},
    {"name": "Trifid Nebula", "target_type": "DSO", "constellation": "Sagittarius", "best_months": ["6", "7", "8", "9"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Nebula with dark lanes dividing glowing gas."},
    {"name": "Eagle Nebula", "target_type": "DSO", "constellation": "Serpens", "best_months": ["6", "7", "8", "9"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Home of the famous Pillars of Creation."},
    {"name": "Omega Nebula", "target_type": "DSO", "constellation": "Sagittarius", "best_months": ["6", "7", "8", "9"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Bright star-forming nebula also known as the Swan Nebula."},
    {"name": "North America Nebula", "target_type": "DSO", "constellation": "Cygnus", "best_months": ["6", "7", "8", "9", "10"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Large nebula; often better as a discussion or imaging target."},
    {"name": "Veil Nebula", "target_type": "DSO", "constellation": "Cygnus", "best_months": ["6", "7", "8", "9", "10"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Supernova remnant; best with dark skies and filters."},
    {"name": "Coathanger Asterism", "target_type": "OTHER", "constellation": "Vulpecula", "best_months": ["6", "7", "8", "9"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Fun binocular object shaped like a coat hanger."},
    {"name": "Albireo", "target_type": "OTHER", "constellation": "Cygnus", "best_months": ["6", "7", "8", "9", "10"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Colorful double star often described as blue and gold."},
    {"name": "Epsilon Lyrae", "target_type": "OTHER", "constellation": "Lyra", "best_months": ["6", "7", "8", "9", "10"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "The famous Double Double star near Vega."},
    {"name": "Summer Triangle", "target_type": "CONSTELLATION", "constellation": "", "best_months": ["6", "7", "8", "9"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Seasonal guide formed by Vega, Deneb, and Altair."},
    {"name": "Sagittarius Teapot", "target_type": "CONSTELLATION", "constellation": "Sagittarius", "best_months": ["6", "7", "8", "9"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Points toward the center of the Milky Way."},
    {"name": "Cygnus", "target_type": "CONSTELLATION", "constellation": "Cygnus", "best_months": ["6", "7", "8", "9", "10"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "The Swan; rich Milky Way constellation."},
    {"name": "Lyra", "target_type": "CONSTELLATION", "constellation": "Lyra", "best_months": ["6", "7", "8", "9", "10"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Small constellation containing Vega and the Ring Nebula."},
    {"name": "Scorpius", "target_type": "CONSTELLATION", "constellation": "Scorpius", "best_months": ["5", "6", "7", "8"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Bright summer constellation with a distinctive curved tail."},
    {"name": "Antares", "target_type": "OTHER", "constellation": "Scorpius", "best_months": ["5", "6", "7", "8"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Red supergiant star and heart of Scorpius."},

    # Fall
    {"name": "Andromeda Galaxy", "target_type": "DSO", "constellation": "Andromeda", "best_months": ["9", "10", "11", "12"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Nearest large galaxy to the Milky Way."},
    {"name": "M15", "target_type": "DSO", "constellation": "Pegasus", "best_months": ["8", "9", "10", "11"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Dense globular cluster in Pegasus."},
    {"name": "M2", "target_type": "DSO", "constellation": "Aquarius", "best_months": ["8", "9", "10", "11"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Large globular cluster visible in fall skies."},
    {"name": "ET Cluster", "target_type": "DSO", "constellation": "Cassiopeia", "best_months": ["9", "10", "11", "12", "1"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Open cluster whose stars resemble a little figure with raised arms."},
    {"name": "Owl Cluster", "target_type": "DSO", "constellation": "Cassiopeia", "best_months": ["9", "10", "11", "12", "1"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Open cluster also known as the Dragonfly Cluster."},
    {"name": "M34", "target_type": "DSO", "constellation": "Perseus", "best_months": ["9", "10", "11", "12"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Open cluster in Perseus."},
    {"name": "M52", "target_type": "DSO", "constellation": "Cassiopeia", "best_months": ["9", "10", "11", "12"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Compact open cluster near Cassiopeia."},
    {"name": "NGC 7789 Caroline's Rose", "target_type": "DSO", "constellation": "Cassiopeia", "best_months": ["9", "10", "11", "12"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Rich open cluster discovered by Caroline Herschel."},
    {"name": "Mirach", "target_type": "OTHER", "constellation": "Andromeda", "best_months": ["9", "10", "11", "12"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Bright star useful for finding the Andromeda Galaxy."},
    {"name": "Almach", "target_type": "OTHER", "constellation": "Andromeda", "best_months": ["9", "10", "11", "12"], "visible_during_event": True, "discussion_only": False, "outreach_notes": "Beautiful colored double star."},
    {"name": "Pegasus Square", "target_type": "CONSTELLATION", "constellation": "Pegasus", "best_months": ["9", "10", "11"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Useful fall asterism for star-hopping."},
    {"name": "Cassiopeia W", "target_type": "CONSTELLATION", "constellation": "Cassiopeia", "best_months": ["9", "10", "11", "12", "1"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Easy-to-recognize W-shaped constellation."},
    {"name": "Perseus", "target_type": "CONSTELLATION", "constellation": "Perseus", "best_months": ["10", "11", "12", "1"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Fall and winter constellation rich with clusters."},
    {"name": "Andromeda", "target_type": "CONSTELLATION", "constellation": "Andromeda", "best_months": ["9", "10", "11", "12"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Home region of the Andromeda Galaxy."},
    {"name": "Aquarius", "target_type": "CONSTELLATION", "constellation": "Aquarius", "best_months": ["8", "9", "10", "11"], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Large zodiac constellation in the fall sky."},

    # Meteor showers
    {"name": "Quadrantid Meteor Shower", "target_type": "METEOR_SHOWER", "constellation": "Boötes", "best_months": ["1"], "visible_during_event": False, "discussion_only": True, "outreach_notes": "Annual meteor shower peaking in early January."},
    {"name": "Lyrid Meteor Shower", "target_type": "METEOR_SHOWER", "constellation": "Lyra", "best_months": ["4"], "visible_during_event": False, "discussion_only": True, "outreach_notes": "Annual April meteor shower."},
    {"name": "Eta Aquariid Meteor Shower", "target_type": "METEOR_SHOWER", "constellation": "Aquarius", "best_months": ["5"], "visible_during_event": False, "discussion_only": True, "outreach_notes": "Meteor shower associated with debris from Halley's Comet."},
    {"name": "Southern Delta Aquariid Meteor Shower", "target_type": "METEOR_SHOWER", "constellation": "Aquarius", "best_months": ["7", "8"], "visible_during_event": False, "discussion_only": True, "outreach_notes": "Summer meteor shower best seen from darker skies."},
    {"name": "Perseid Meteor Shower", "target_type": "METEOR_SHOWER", "constellation": "Perseus", "best_months": ["8"], "visible_during_event": False, "discussion_only": True, "outreach_notes": "Popular annual meteor shower peaking in August."},
    {"name": "Orionid Meteor Shower", "target_type": "METEOR_SHOWER", "constellation": "Orion", "best_months": ["10"], "visible_during_event": False, "discussion_only": True, "outreach_notes": "Meteor shower associated with debris from Halley's Comet."},
    {"name": "Leonid Meteor Shower", "target_type": "METEOR_SHOWER", "constellation": "Leo", "best_months": ["11"], "visible_during_event": False, "discussion_only": True, "outreach_notes": "Annual meteor shower famous for occasional meteor storms."},
    {"name": "Geminid Meteor Shower", "target_type": "METEOR_SHOWER", "constellation": "Gemini", "best_months": ["12"], "visible_during_event": False, "discussion_only": True, "outreach_notes": "Strong annual meteor shower peaking in December."},

    # Discussion topics
    {"name": "Light Pollution", "target_type": "OTHER", "constellation": "", "best_months": [], "visible_during_event": False, "discussion_only": True, "outreach_notes": "Good discussion topic for sky brightness, dark skies, and responsible lighting."},
    {"name": "Milky Way Structure", "target_type": "OTHER", "constellation": "", "best_months": ["6", "7", "8", "9"], "visible_during_event": False, "discussion_only": True, "outreach_notes": "Explains our place inside a spiral galaxy."},
    {"name": "Scale of the Universe", "target_type": "OTHER", "constellation": "", "best_months": [], "visible_during_event": False, "discussion_only": True, "outreach_notes": "Useful for explaining distances, light-years, and cosmic scale."},
    {"name": "Why Stars Twinkle", "target_type": "OTHER", "constellation": "", "best_months": [], "visible_during_event": False, "discussion_only": True, "outreach_notes": "Explains how Earth's atmosphere distorts starlight."},
    {"name": "Stellar Evolution", "target_type": "OTHER", "constellation": "", "best_months": [], "visible_during_event": False, "discussion_only": True, "outreach_notes": "Connects nebulae, star clusters, red giants, and white dwarfs."},
    {"name": "Black Holes", "target_type": "OTHER", "constellation": "", "best_months": [], "visible_during_event": False, "discussion_only": True, "outreach_notes": "Popular public topic for gravity, compact objects, and galaxies."},
    {"name": "Exoplanets", "target_type": "OTHER", "constellation": "", "best_months": [], "visible_during_event": False, "discussion_only": True, "outreach_notes": "Good public topic for planets around other stars."},
    {"name": "How Telescopes Work", "target_type": "OTHER", "constellation": "", "best_months": [], "visible_during_event": False, "discussion_only": True, "outreach_notes": "Explains mirrors, lenses, aperture, and magnification."},
    {"name": "Why Pluto Is a Dwarf Planet", "target_type": "OTHER", "constellation": "", "best_months": [], "visible_during_event": False, "discussion_only": True, "outreach_notes": "Good conversation starter about how science classifies objects."},
    {"name": "How We Find North", "target_type": "OTHER", "constellation": "", "best_months": [], "visible_during_event": False, "discussion_only": True, "outreach_notes": "Uses Polaris, circumpolar stars, and Earth's rotation."},
    {"name": "Moon Phases", "target_type": "MOON", "constellation": "", "best_months": [], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Explains why the Moon changes shape through the month."},
    {"name": "Craters and Maria", "target_type": "MOON", "constellation": "", "best_months": [], "visible_during_event": True, "discussion_only": True, "outreach_notes": "Good topic when the Moon is visible."},
]


class Command(BaseCommand):
    help = "Seed default astronomical outreach targets."

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for target_data in DEFAULT_TARGETS:
            target, created = AstronomicalTarget.objects.update_or_create(
                name=target_data["name"],
                defaults=target_data,
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete. Created: {created_count}. Updated: {updated_count}."
            )
        )