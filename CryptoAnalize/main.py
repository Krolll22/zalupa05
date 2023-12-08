from f_account import account_is_valid, get_account_tokens_balance_moralis, get_account_token_profit, \
    get_account_eth_balance
from f_tokens import *
from f_utils import timing_decorator, print_divider


def get_wallet_profit(wallet_for_check):
    acc_profit = get_account_token_profit(wallet_for_check) + get_account_eth_balance(
        wallet_for_check) + get_account_tokens_balance_moralis(wallet_for_check)
    print(f'Итоговый профит для кошелька: {wallet_for_check} равен = {acc_profit}')
    return acc_profit


@timing_decorator
def main():
    wallets = [
    '0x71423f30eb82f25e3351ce6e65048d76756a718f',
    '0x1b842b8b538c82f050bdabdf92eb5c7c5d65a2db',
    '0x6c1573335416a2df7b146ffd2b4f501e9bec2c6d',
    '0x3285eb29ef419dd0891dcfa866c0d4f1fbd5e0ac',
    '0xfc049433ac9b8b7e0cac465130a5b3c7860c4c3f',
    '0xbf4268fa39798108395d5077ae020d3bbc13cdd2',
    '0xbf4268fa39798108395d5077ae020d3bbc13cdd2',
    '0xbf4268fa39798108395d5077ae020d3bbc13cdd2',
    '0x3833aec21fa7b4910e0369ed41e8c74467c82c14',
    '0xbf4268fa39798108395d5077ae020d3bbc13cdd2',
    '0xb230fad06a1fffd9fe7378eeb78394e7e99c8209',
    '0xbf4268fa39798108395d5077ae020d3bbc13cdd2',
    '0xbf4268fa39798108395d5077ae020d3bbc13cdd2',
    '0x47cd21866620f8121104c8f6c7ee1d946a6e1a36',
    '0xf7431e4aed80f2ace7e0a903b16ec20d72609ea5',
    '0x0d48006368a0b990bf08219a1a14950921da796a',
    '0xbec010c2a20e24e10fb86226dc415fe5cd935547',
    '0x1952b14ebe9e2dd123123f84fd2d0f9660ade726',
    '0xa6c70679050189f65d86c6ee8ec5a90a61fbc09e',
    '0x5798ad9dd765276e2d3eaf54e6309e5e4a2ef37e',
    '0xa1fb1642e9cf277ae647f5ca185b5f25ba579b6c',
    '0xfc049433ac9b8b7e0cac465130a5b3c7860c4c3f',
    '0x950af48887030bb4bd90366e9feb6dac7c32618b',
    '0xdecfce6476a66bf8cb1a9f3005ce5496363a99de',
    '0xc7098330aa8b36d687d5d55cc76a8a4495e12348',
    '0x03f9d4ad9faeec3376a9feb553c6ddc42468733c',
    '0xd8708f3a041feb7f50ecc0e7404ce0319c05946b',
    '0x006ded6f999e031c2131429e989e75bc3474674b',
    '0xafdc7168053efbdcf06ec147d7d77ce3d6cbaf40',
    '0x3b55d798d1658f3c44c111354de654c3c8b530e3',
    '0xccd6538b09af1110e9d17fde5a3238ffa4c8aa7e',
    '0xe6960cc5d50b9e021c1b5436659273ae5b116973',
    '0xe6960cc5d50b9e021c1b5436659273ae5b116973',
    '0x24b7cf66fa687d14f254016181f89bbd3b495ce3',
    '0xc5c9f6dda68422984a06a66a3d1aebd7d979a158',
    '0xbcbe368e75c77bfec82d4bda216e52efdd0c5a6f',
    '0x2875c22790b7a2b0ec9c4e72ff419c51fa117702',
    '0x65c6ad24460944f0e6878e5dc4b007e0dd093590',
    '0x5a8562c5192f1d0fba678006c57b60ac50bbcb94',
    '0x031c0e231b5ce67a8e105fa55a9e2f95711da8c4',
    '0x2952c225639041f920722fdb71044baa824c22c2',
    '0xa300c33db7f1902d4d2e38636c9b0ddf548da2ca',
    '0x5e07310acc4935e7739bd91cf578e0ae1fad9e2a',
    '0x16f39f8ff59caead81bc680e6cd663069eb978be',
    '0xf832ff70e23f33584594dd5bdd261473c69bb105',
    '0xf294c1bf56b8020d4b3a0e5816228953e2892823',
    ]
    profit_wallets = []
    for wallet in wallets:
        try:
            if account_is_valid(wallet):
                print(f'Wallet: {wallet} | isValid: True')
                print_divider()
                profit = get_wallet_profit(wallet.lower())
                if profit is not None and profit > 0:
                    profit_wallets.append({'wallet': wallet.lower(), 'profit': profit})
            else:
                print(f'Wallet: {wallet} | isValid: False')
        except Exception as e:
            print(f"Error for wallet {wallet}: {str(e)}")
    try:
        now = int(time.time())
        with open(f'profit_wallets_{now}.txt', 'w') as f:
            for wallet in profit_wallets:
                f.write(f"{wallet['wallet']} | Profit: {wallet['profit']}\n")
    except Exception as e:
        print(f"Error writing to file: {str(e)}")
        for wallet in profit_wallets:
            print(wallet)


main()