import time
import math
from minecraft.networking.packets.serverbound.play import (
    PlayerDiggingPacket,
    UseEntityPacket,
    AnimationPacket,
)
from minecraft.networking.packets.clientbound.play import (
    SpawnMobPacket,
    EntityTeleportPacket,
    EntityDestroyPacket,
)
from minecraft.networking.types import Position

# Minerar um bloco
def mine_block(connection, x, y, z, face=1, dig_time=1.5):
    start_dig = PlayerDiggingPacket()
    start_dig.status = 0  # Iniciar mineração
    start_dig.position = Position(x, y, z)
    start_dig.face = face
    connection.write_packet(start_dig)
    time.sleep(dig_time)
    finish_dig = PlayerDiggingPacket()
    finish_dig.status = 2  # Terminar mineração
    finish_dig.position = Position(x, y, z)
    finish_dig.face = face
    connection.write_packet(finish_dig)

# Atacar o mob mais próximo
def attack_nearest_mob(connection, bot_x, bot_y, bot_z, max_distance=16):
    entities = {}

    def handle_spawn_mob(packet):
        entities[packet.entity_id] = (packet.x, packet.y, packet.z)

    def handle_entity_teleport(packet):
        if packet.entity_id in entities:
            entities[packet.entity_id] = (packet.x, packet.y, packet.z)

    def handle_entity_destroy(packet):
        for entity_id in packet.entity_ids:
            if entity_id in entities:
                del entities[entity_id]

    connection.register_packet_listener(handle_spawn_mob, SpawnMobPacket)
    connection.register_packet_listener(handle_entity_teleport, EntityTeleportPacket)
    connection.register_packet_listener(handle_entity_destroy, EntityDestroyPacket)

    time.sleep(1)  # Pequena espera para coletar entidades

    nearest = None
    nearest_dist = max_distance + 1
    for entity_id, (x, y, z) in entities.items():
        dx = x - bot_x
        dy = y - bot_y
        dz = z - bot_z
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        if dist <= max_distance and dist < nearest_dist:
            nearest = entity_id
            nearest_dist = dist

    if nearest is not None:
        packet = UseEntityPacket()
        packet.entity_id = nearest
        packet.type = UseEntityPacket.TYPE_ATTACK
        connection.write_packet(packet)
        swing_arm(connection)
    else:
        print("Nenhum mob próximo para atacar.")

# Bater (animar braço)
def swing_arm(connection):
    animation = AnimationPacket()
    animation.entity_id = 0  # 0 = o próprio jogador
    animation.animation = 0  # 0 = braço balançando
    connection.write_packet(animation)

# Respawn real (sem /respawn)
def respawn_real(connection):
    from minecraft.networking.packets.serverbound.play import ClientStatusPacket
    packet = ClientStatusPacket()
    packet.action_id = 0  # Perform respawn
    connection.write_packet(packet)
    print("✅ Respawn enviado (ClientStatusPacket)")

# Abrir baú (apenas envia 'use' na entidade próxima - Exemplo genérico)
def open_chest_real(connection):
    # Exemplo: Você teria que detectar a posição do baú manualmente
    print("✅ Exemplo: Para abrir um baú, use 'use_entity' com o chest se ele for entidade (ex: Shulker Box custom).")
    # Caso precise posso detalhar pra containers específicos.

# Olhar para uma posição
def look_at_target(connection, target_x, target_y, target_z):
    print(f"🧭 Girando para olhar para: {target_x}, {target_y}, {target_z}")
    # Implementar envio de posição + ângulo de visão (preciso saber sua posição atual para fazer o cálculo real)

# Dropar itens (drop all do inventário: envio vários drops, exemplo fake)
def drop_all_items(connection):
    print("🚮 Dropando todos os itens (Exemplo básico: sem manipular inventário real ainda)")
    # Aqui você precisa implementar ClickWindowPacket para mover os itens.

# Auto equipar (Exemplo básico de mudar item ativo na hotbar)
def auto_equip_item(connection, hotbar_slot):
    from minecraft.networking.packets.serverbound.play import HeldItemChangePacket
    packet = HeldItemChangePacket()
    packet.slot = hotbar_slot
    connection.write_packet(packet)
    print(f"✅ Equipado item no slot {hotbar_slot} da hotbar.")

# Pegar itens caídos próximos (Exemplo simples de interação com entidades do tipo Item)
def pickup_nearby_items(connection):
    print("✅ (Exemplo) Para pegar itens: envie movimento até o item e o cliente coleta automático se passar por cima.")

# Caminhar em uma direção (movimentar)
def auto_walk(connection, direction_vector, duration=2.0):
    print(f"🚶 Andando na direção {direction_vector} por {duration} segundos (movimento real precisa enviar pacotes de movimento).")

# Usar item na mão (exemplo genérico - swing_arm + talvez interaction packet dependendo da versão)
def use_item_in_hand(connection):
    print("✅ Usando item na mão (Swing de braço, pode combinar com interact packet).")
    swing_arm(connection)