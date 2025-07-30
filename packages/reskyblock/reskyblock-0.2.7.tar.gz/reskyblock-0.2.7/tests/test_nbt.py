import pytest

from reskyblock.nbt import DecodedNBT

_BULK_NBTS: list[str] = (
    (__import__("pathlib").Path(__file__).resolve().parents[0] / "data" / "item_bytes.txt").read_text().split("\n")[:-1]
)


def test_item_simple() -> None:
    raw_data = "H4sIAAAAAAAAAE1SzW7aQBAeIGkAqWmPlXqopaa3uLJxwPjQgws0GGG7hL/Yl2rZXWDJro3sNQm8Q54jL9AniPpcVZfk0tNov5/5dkZTB6hBidUBoFSGMiOlxxKcdtIikaU6VCRaVaDWZ4T+4GiVK9XfOtTHdwXn4X1CsyqUPQIXJrathdXEOsXE0q2l7ejIdpCOW21qN9pX5qLZUr6fWbqlmWQ0r0FV0gdZZDR/ia7C6QzxgsJvuh8Y8e3aILcDjvdeS70nY4OH3mZre8lsv+h4LU8ovu+2hnvnP21TonmTR9ZgHSejYiFmxtC64bR/Y2Ix3UUH1wqvo0O88Yxo07OCzXcRzkdGNB8wv7sy/fmMKb4RHchdLGIRKiyY4Pvwetrwu6Nm3O2Z8bV/729cwxeDddgdHQI2cJa3xjc1QR3OCMu3HO1rcDJMM1pV4Bl8fn6y1dQ7tcBcY0IUCZN7Da0QS3KpESTQisJHJVpmqdCen1KRKvz5CQ/RDin4q+piqTpfM041lmhyTY90J2MiTxPNyzlV9KW2ylAicw0pEjWML/BJVUW8JmgZJQWWTBmOuRSRY98PLxI+DTqh74eB5nY6vfE4vImqcBIgQeG9Ehz/oU0QZ7lAiZryXe9BZsiVMmOLQtK8erwZeDt0Z+6viTv0xr4bKH9RKPSiQRzcNBaGbpOWqV/ZiOiOg9u6YZlLSjGy8ZKeQE0yQXOJxFYdwuP55fkfgDK86b4upwLwD93/ZTikAgAA"
    did = DecodedNBT(raw_data)
    assert did
    assert did.skyblock_id == "LAVA_TALISMAN"
    assert did.enchantments == []
    assert did.art_of_war_count == 0
    assert did.rarity_upgrades == 0
    assert not did.is_pet
    assert did.reforge is None
    assert did.dungeon_stars == 0
    assert did.scrolls == []


def test_item_pet() -> None:
    raw_data = "H4sIAAAAAAAAAI1Uz2/iRhQekmwXUKVVVyv1x2lqbQ/V4nRsY4Mj9cAGShwBYVmSAFUPg/3Aztpjao8ToOqfsD1WPfTOsarUQ8/8Kfkfel31mURRpF4qjTR+P773fe+NZ8qElEghKBNCCntkL/AK7wvkyXGcCVkok33J5/ukdBJ48F3I5ylmfSiT8tt3WRie3QhIimTP8chL3TJZXa9Zqss0rho6t1VbZ5pa8zhoNb1qm1VAXD+JF5DIANISKUpYyiyBdEddJE8ueJgB+QtWp2wy8pk3Og3dlWOhPXzLwjPnalFzxMVqeuxYToTxk4bVWdmPck3JL81wbJz6E/Emm0YXrGMMQjgZaG50ft29cpbdpqP1ml3Wbb7RxtHA760bq96ls54Mz5e9trPuDic+7kZv/fqqF0388XAQjIehP2k7bBydr8+aDbM3dPRJnqOPzcnxqT0bsW+xgzJ56gXpIuSrEjnoxAkU0fkp+WS7qbeE63MhAzGnfZDofr7d1JowA5HCEd1u+CuTkc/Q5wgJYRjMQbj3AY0xzP94u7E6PIVkCjwiGmbimvBFSldxllAQEOFI6SxOEDTV2RK32i6E5u3vvxAF98fF8zhcQ7LKSYwUrUOk+QJpHmm9DFIvjujrOE4l+eaOFFc7wXiKQOOVwW5/+4P+B3JfLlfd5YLTfhyH5PAOPQAUAAmXuYapwb7aSVnKhNMIcyvUi7NpCB75HP03PggqgCcUOwsEvUFYkpd+htjtJuw2RrTTumh1yAsc8+2vf1PdrNh1raLVGR31MfHrHSsMgrkvVTcM3HdUxpR7HpV+kNIFyNzOR5XLhdyOQGRf3nFYyNFptVu9ZmMwLpKDHo9gd1Dfd65DimfzA6q32hlPvIAL/AWetfJOGlImwTSTkBbJUyzpiFlM/vlJkasFKEdK+7wxaDqNnlJRuCuDa/TNeJhCRYHlQjnSD01sATuoG6ZhGLpttmoVBe9MgtgHNQj28VLmpR/gLhfe6jwFTzliFSXLAvxQ7NpU03kd1JluW2qVV+uqDTZTTV616vWqZ7AZw2KZCH7MwMkRVeCeVp9OVdPVa2pVY5Zqc3emzpjF8SJzw+DVe/rdXI/zsT6IEHE3fmjp52L+opD9fmuI48sVkZf/R9ABKckgglTyaIGPw/vnH/50CNkjHzV5xOdA9gn5F2U272a4BAAA"
    did = DecodedNBT(raw_data)
    assert did
    assert did.skyblock_id == "GUARDIAN_PET"
    assert did.enchantments == []
    assert did.art_of_war_count == 0
    assert did.rarity_upgrades == 0
    assert did.is_pet
    assert did.reforge is None
    assert did.dungeon_stars == 0
    assert did.scrolls == []


def test_item_hyperion() -> None:
    raw_data = "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"
    did = DecodedNBT(raw_data)
    assert did
    assert did.skyblock_id == "HYPERION"
    assert did.enchantments == [
        "ENCHANTMENT_IMPALING_3",
        "ENCHANTMENT_LUCK_6",
        "ENCHANTMENT_CRITICAL_6",
        "ENCHANTMENT_CLEAVE_6",
        "ENCHANTMENT_SMOLDERING_2",
        "ENCHANTMENT_LOOTING_4",
        "ENCHANTMENT_SYPHON_4",
        "ENCHANTMENT_SMITE_7",
        "ENCHANTMENT_SCAVENGER_4",
        "ENCHANTMENT_ENDER_SLAYER_7",
        "ENCHANTMENT_FIRE_ASPECT_3",
        "ENCHANTMENT_VAMPIRISM_6",
        "ENCHANTMENT_EXPERIENCE_4",
        "ENCHANTMENT_EXECUTE_5",
        "ENCHANTMENT_GIANT_KILLER_6",
        "ENCHANTMENT_VENOMOUS_5",
        "ENCHANTMENT_DRAGON_HUNTER_1",
        "ENCHANTMENT_FIRST_STRIKE_4",
        "ENCHANTMENT_THUNDERLORD_7",
        "ENCHANTMENT_ULTIMATE_WISE_5",
        "ENCHANTMENT_CUBISM_5",
        "ENCHANTMENT_CHAMPION_10",
        "ENCHANTMENT_LETHALITY_6",
    ]
    assert did.art_of_war_count == 1
    assert did.rarity_upgrades == 1
    assert not did.is_pet
    assert did.reforge == "heroic"
    assert did.dungeon_stars == 9
    assert did.scrolls == [
        "WITHER_SHIELD_SCROLL",
        "SHADOW_WARP_SCROLL",
        "IMPLOSION_SCROLL",
    ]

    assert did.dict() == {
        "Count": 1,
        "Damage": 0,
        "id": 267,
        "tag": {
            "ExtraAttributes": {
                "ability_scroll": None,
                "art_of_war_count": 1,
                "champion_combat_xp": 72582071.63017021,
                "enchantments": {
                    "champion": 10,
                    "cleave": 6,
                    "critical": 6,
                    "cubism": 5,
                    "dragon_hunter": 1,
                    "ender_slayer": 7,
                    "execute": 5,
                    "experience": 4,
                    "fire_aspect": 3,
                    "first_strike": 4,
                    "giant_killer": 6,
                    "impaling": 3,
                    "lethality": 6,
                    "looting": 4,
                    "luck": 6,
                    "scavenger": 4,
                    "smite": 7,
                    "smoldering": 2,
                    "syphon": 4,
                    "thunderlord": 7,
                    "ultimate_wise": 5,
                    "vampirism": 6,
                    "venomous": 5,
                },
                "gems": {
                    "COMBAT_0": "FINE",
                    "COMBAT_0_gem": "SAPPHIRE",
                    "DEFENSIVE_0": {"quality": "PERFECT", "uuid": "84c26564-2981-431f-9051-273668a0af50"},
                    "DEFENSIVE_0_gem": "AMETHYST",
                    "SAPPHIRE_0": "FINE",
                    "unlocked_slots": None,
                },
                "hot_potato_count": 15,
                "id": "HYPERION",
                "modifier": "heroic",
                "rarity_upgrades": 1,
                "stats_book": 177662,
                "timestamp": 1657706160000,
                "upgrade_level": 9,
                "uuid": "21616c2d-6a14-4690-9b52-8d1857ed30cb",
            },
            "HideFlags": 254,
            "Unbreakable": 1,
            "display": {"Lore": None, "Name": "§dHeroic Hyperion §6✪§6✪§6✪§6✪§6✪§c➍"},
            "ench": None,
        },
    }


@pytest.mark.parametrize("raw_data", _BULK_NBTS)
def test_bulk_nbts(raw_data: str) -> None:
    DecodedNBT(raw_data)


@pytest.mark.parametrize("raw_data", _BULK_NBTS)
def test_bulk_nbts_dicts(raw_data: str) -> None:
    DecodedNBT(raw_data).dict()
