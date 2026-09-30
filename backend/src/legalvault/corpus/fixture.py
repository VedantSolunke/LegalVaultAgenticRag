from legalvault.models.research import SectionRecord

FIXTURE_SECTIONS: tuple[SectionRecord, ...] = (
    SectionRecord(
        section_number=101,
        title="Murder",
        chapter="VI — Of Offences Affecting The Human Body",
        text=(
            "Whoever commits murder shall be punished with death or imprisonment "
            "for life, and shall also be liable to fine."
        ),
    ),
    SectionRecord(
        section_number=103,
        title="Punishment for murder",
        chapter="VI — Of Offences Affecting The Human Body",
        text=(
            "Whoever commits murder shall be punished with death or imprisonment "
            "for life, and shall also be liable to fine."
        ),
    ),
    SectionRecord(
        section_number=115,
        title="Abetment of suicide of child or person of unsound mind",
        chapter="V — Of Abetment",
        text=(
            "Whoever abets the commission of suicide by a child or by a person "
            "who is in a state of intoxication or who has unsoundness of mind, "
            "shall be punished with death or imprisonment for life, or with "
            "imprisonment of either description for a term which may extend to "
            "ten years, and shall also be liable to fine."
        ),
    ),
)

FIXTURE_SECTION_NUMBERS: list[int] = [s.section_number for s in FIXTURE_SECTIONS]
